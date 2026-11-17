<?php

namespace App;

use Aws\Sqs\SqsClient;
use Aws\Exception\AwsException;

class OrderProducer
{
    public function __construct(
        private SqsClient $sqsClient,
        private string $queueUrl
    ) {}

    public function sendOrder(string $orderId, int $price, int $quantity): bool
    {
        // Python側の OrderWorker が期待するキー名で配列を作成
        $payload = [
            'order_id' => $orderId,
            'price'    => $price,
            'quantity' => $quantity,
        ];

        try {
            $this->sqsClient->sendMessage([
                'QueueUrl'    => $this->queueUrl,
                'MessageBody' => json_encode($payload, JSON_THROW_ON_ERROR),
            ]);

            return true;
        } catch (AwsException | \JsonException $e) {
            // 実務ではここでエラーログを記録します
            return false;
        }
    }
}
