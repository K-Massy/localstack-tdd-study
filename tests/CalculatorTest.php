<?php

namespace Tests;

use PHPUnit\Framework\TestCase;
use App\Calculator;

class CalculatorTest extends TestCase
{
    public function test_足し算が正しく計算できること(): void
    {
        // 1. 準備（テストしたいクラスを用意）
        $calculator = new Calculator();

        // 2. 実行（2 + 3 を計算させる）
        $result = $calculator->add(2, 3);

        // 3. 検証（「結果が 5 になるはずだ！」とロボットに判定させる）
        $this->assertSame(5, $result);
    }
}
