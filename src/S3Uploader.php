<?php

namespace App;

use Aws\S3\S3Client;

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
        } catch (\Exception $e) {
            return false;
        }
    }
}
