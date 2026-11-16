import json
import boto3
import pytest
from python_src.order_worker import OrderWorker


@pytest.fixture
def sqs_setup():
    """PHPUnitの setUp() に相当する事前準備関数"""
    # 1. LocalStackのSQSに接続するクライアントを作成
    sqs_client = boto3.client(
        "sqs",
        region_name="ap-northeast-1",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="dummy",
        aws_secret_access_key="dummy",
    )

    # 2. テスト用のSQSキュー（郵便受け）を作成してURLを取得
    response = sqs_client.create_queue(QueueName="test-order-queue")
    queue_url = response["QueueUrl"]

    # テスト関数へ sqs_client と queue_url を渡す
    yield sqs_client, queue_url

    # 3. テスト終了後の後片付け（キューを削除して毎回クリーンな状態に保つ）
    sqs_client.delete_queue(QueueUrl=queue_url)


def test_SQSから注文メッセージを受信して税込合計金額を計算できること(sqs_setup):
    # 1. 準備 (Arrange)
    sqs_client, queue_url = sqs_setup

    # SQSにテスト用の注文データ（JSON）を1件送信しておく
    order_data = {"order_id": "ORD-001", "price": 1000, "quantity": 2}
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(order_data),
    )

    # これから作る本番クラス（DIで sqs_client と queue_url を渡す）
    worker = OrderWorker(sqs_client=sqs_client, queue_url=queue_url)

    # 2. 実行 (Act)
    result = worker.process_next_order()

    # 3. 検証 (Assert)
    # 1000円 × 2個 × 消費税10% = 2200円 になるはず
    assert result == {
        "order_id": "ORD-001",
        "total_amount": 2200,
    }

    # 処理完了後、SQSキューからメッセージが完全に削除されているはず（隠れているだけの状態も許さない）
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=[
            "ApproximateNumberOfMessages",           # 見えているメッセージ数
            "ApproximateNumberOfMessagesNotVisible", # 処理中（隠れている）メッセージ数
        ],
    )["Attributes"]

    assert int(attributes["ApproximateNumberOfMessages"]) == 0
    assert int(attributes["ApproximateNumberOfMessagesNotVisible"]) == 0

def test_不正なJSONメッセージを受信した場合はNoneを返しメッセージを削除しないこと(sqs_setup):
    # 1. 準備 (Arrange)
    sqs_client, queue_url = sqs_setup

    # JSONとして壊れている不正な文字列をキューに送信する
    sqs_client.send_message(
        QueueUrl=queue_url,
        MessageBody="{invalid-json-data...",
    )

    worker = OrderWorker(sqs_client=sqs_client, queue_url=queue_url)

    # 2. 実行 (Act)
    result = worker.process_next_order()

    # 3. 検証 (Assert)
    # ① クラッシュせずに None が返ってくること
    assert result is None

    # ② 処理に失敗しているので、メッセージは削除されずキューに残っていること（処理中＝1件）
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["ApproximateNumberOfMessagesNotVisible"],
    )["Attributes"]
    assert int(attributes["ApproximateNumberOfMessagesNotVisible"]) == 1
