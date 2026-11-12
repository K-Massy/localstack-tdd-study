<?php

namespace Tests;

use PHPUnit\Framework\TestCase;
use Aws\S3\S3Client;
use App\S3Uploader;

class S3UploaderTest extends TestCase
{
    private S3Client $s3Client;
    private string $bucketName = 'tdd-test-bucket';

    // 各テストが実行される直前に毎回自動で呼ばれる初期化メソッド
    protected function setUp(): void
    {
        parent::setUp();

        // 1. 本物のAWSではなく、手元のLocalStackに接続するためのクライアント設定
        $this->s3Client = new S3Client([
            'version'                 => 'latest',
            'region'                  => 'ap-northeast-1',
            'endpoint'                => 'http://localhost:4566', // LocalStackの窓口
            'use_path_style_endpoint' => true,                    // LocalStack必須のおまじない
            'credentials'             => [
                'key'    => 'dummy',
                'secret' => 'dummy',
            ],
        ]);

        // 2. テスト用のS3バケット（フォルダ）をLocalStack上に作成する
        // （すでに存在している場合のエラーを防ぐため try-catch で囲む）
        try {
            $this->s3Client->createBucket(['Bucket' => $this->bucketName]);
        } catch (\Exception $e) {
            // すでにバケットがある場合は何もしない
        }
    }

    public function test_LocalStackのS3にテキストファイルが正しくアップロードできること(): void
    {
        // 1. 準備 (Arrange)
        $uploader = new S3Uploader($this->s3Client);
        $fileName = 'hello.txt';
        $content  = 'Hello, LocalStack TDD!';

        // 2. 実行 (Act)
        $isSuccess = $uploader->upload($this->bucketName, $fileName, $content);

        // 3. 検証 (Assert)
        // ① uploadメソッド自体が true を返しているか？
        $this->assertTrue($isSuccess);

        // ② 実際にLocalStack（S3）からファイルを取得して、中身が一致しているか？
        $result = $this->s3Client->getObject([
            'Bucket' => $this->bucketName,
            'Key'    => $fileName,
        ]);
        $this->assertSame($content, (string) $result['Body']);
    }
}
