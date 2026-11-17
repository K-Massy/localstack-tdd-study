<?php

namespace Tests;

use PHPUnit\Framework\TestCase;
use Aws\Sqs\SqsClient;
use App\OrderProducer;

class OrderProducerTest extends TestCase
{
    private SqsClient $sqsClient;
    private OrderProducer $producer;
    private string $queueUrl;

    protected function setUp(): void
    {
        parent::setUp();

        // 1. LocalStackのSQSクライアントを初期化
        $this->sqsClient = new SqsClient([
            'version'     => 'latest',
            'region'      => 'ap-northeast-1',
            'endpoint'    => 'http://localhost:4566',
            'credentials' => [
                'key'    => 'dummy',
                'secret' => 'dummy',
            ],
        ]);

        // 2. テスト用キューを作成してURLを取得
        $result = $this->sqsClient->createQueue([
            'QueueName' => 'php-to-python-order-queue' . uniqid(),
        ]);
        $this->queueUrl = $result['QueueUrl'];

        // キューに古いメッセージが残っていたら空にしておく
        $this->sqsClient->purgeQueue(['QueueUrl' => $this->queueUrl]);

        // 3. これから作るPHP本番クラスを初期化
        $this->producer = new OrderProducer($this->sqsClient, $this->queueUrl);
    }

    public function test_注文データをJSON形式でSQSキューに送信できること(): void
    {
        // 1. 準備 (Arrange)
        $orderId  = 'ORD-2026-999';
        $price    = 3000;
        $quantity = 2;

        // 2. 実行 (Act)
        $isSuccess = $this->producer->sendOrder($orderId, $price, $quantity);

        // 3. 検証 (Assert)
        $this->assertTrue($isSuccess);

        // 実際にSQSからメッセージを取り出して、Python側が期待するJSONになっているか確認
        $received = $this->sqsClient->receiveMessage([
            'QueueUrl'            => $this->queueUrl,
            'MaxNumberOfMessages' => 1,
        ]);

        $this->assertNotEmpty($received['Messages']);
        $decodedBody = json_decode($received['Messages'][0]['Body'], true);

        $this->assertSame([
            'order_id' => 'ORD-2026-999',
            'price'    => 3000,
            'quantity' => 2,
        ], $decodedBody);
    }
}
