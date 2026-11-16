<?php

namespace App;

use Aws\S3\S3Client;
use Aws\Exception\AwsException;

class S3Uploader
{
    public function __construct(
        private S3Client $s3Client
    ) {}

    public function upload(string $bucketName, string $fileName, string $content): bool
    {
        try {
            $this->s3Client->putObject([
                'Bucket' => $bucketName,
                'Key'    => $fileName,
                'Body'   => $content,
            ]);

            return true;
        } catch (AwsException $e) {
            // 実務ではここでエラーログ（error_log や Monolog など）を記録します
//            error_log('S3 Upload Error: ' . $e->getMessage());
            return false;
        }
    }
}
