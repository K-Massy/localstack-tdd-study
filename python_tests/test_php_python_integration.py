import subprocess
import uuid
import boto3
import pytest
from python_src.order_worker import OrderWorker


@pytest.fixture
def integration_sqs_setup():
    """PHPとPythonが共通で使う一意のSQSキューを準備する"""
    sqs_client = boto3.client(
        "sqs",
        region_name="ap-northeast-1",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )

    # PHP側の uniqid() と同じく、uuid4() で毎回一意のキュー名を生成
    queue_name = f"php-python-e2e-queue-{uuid.uuid4().hex[:8]}"
    response = sqs_client.create_queue(QueueName=queue_name)
    queue_url = response["QueueUrl"]

    yield sqs_client, queue_url

    # テスト終了後にキューを削除して後片付け
    sqs_client.delete_queue(QueueUrl=queue_url)


def test_PHPが送信した注文データをPythonワーカーが受信して税込計算と削除を完了できること(integration_sqs_setup):
    # 1. 準備 (Arrange)
    sqs_client, queue_url = integration_sqs_setup

    # PHPのワンライナーコードを用意（2週目・4週目で作ったPHPクラスを実際に動かす）
    php_code = f"""
    require 'vendor/autoload.php';
    use Aws\\Sqs\\SqsClient;
    use App\\OrderProducer;

    $client = new SqsClient([
        'version'     => 'latest',
        'region'      => 'ap-northeast-1',
        'endpoint'    => 'http://localhost:4566',
        'credentials' => ['key' => 'dummy', 'secret' => 'dummy'],
    ]);

    $producer = new OrderProducer($client, '{queue_url}');
    $ok = $producer->sendOrder('ORD-E2E-777', 5000, 3);
    if (!$ok) {{ exit(1); }}
    """

    # 2. 実行 (Act)
    # ① まずPHP側（受付プロデューサー）を実行してSQSに注文を送信させる
    php_result = subprocess.run(
        ["php", "-r", php_code],
        capture_output=True,
        text=True,
    )
    assert php_result.returncode == 0, f"PHP実行エラー: {php_result.stderr}"

    # ② 次にPython側（バッチワーカー）を実行してSQSから注文を取り出し処理する
    worker = OrderWorker(sqs_client=sqs_client, queue_url=queue_url)
    processed_order = worker.process_next_order()

    # 3. 検証 (Assert)
    # ① PHPが送った「5000円 × 3個」をPythonが正しく税込計算（16500円）できていること
    assert processed_order == {
        "order_id": "ORD-E2E-777",
        "total_amount": 16500,
    }

    # ② 処理完了後、SQSキューからメッセージが完全に削除されていること
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=[
            "ApproximateNumberOfMessages",
            "ApproximateNumberOfMessagesNotVisible",
        ],
    )["Attributes"]
    assert int(attributes["ApproximateNumberOfMessages"]) == 0
    assert int(attributes["ApproximateNumberOfMessagesNotVisible"]) == 0
