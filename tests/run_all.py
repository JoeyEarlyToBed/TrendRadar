#!/usr/bin/env python3
"""
TrendRadar 全量测试运行器
运行所有 tests/test_*.py 中的测试用例
"""
import sys
import os
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def run_tests():
    """运行所有测试文件"""
    test_files = sorted(
        f for f in os.listdir(HERE)
        if f.startswith("test_") and f.endswith(".py") and f != "run_all.py"
    )

    print("=" * 70)
    print(f"  TrendRadar 测试运行器 — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  发现 {len(test_files)} 个测试文件")
    print("=" * 70)

    results = []
    for tf in test_files:
        path = os.path.join(HERE, tf)
        print(f"\n{'─' * 70}")
        print(f"  ▶ {tf}")
        print(f"{'─' * 70}")

        start = time.time()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", path, "-v", "--tb=short"],
            capture_output=True, text=True, cwd=ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        elapsed = time.time() - start

        # Filter LiteLLM noise
        output_lines = []
        for line in (result.stdout + result.stderr).split("\n"):
            if "LiteLLM" not in line and "Failed to fetch" not in line:
                output_lines.append(line)

        output = "\n".join(output_lines)
        passed = result.returncode == 0
        results.append((tf, passed, elapsed, output))

        if passed:
            print(f"  ✅ {tf} — {elapsed:.1f}s (PASS)")
        else:
            print(f"  ❌ {tf} — {elapsed:.1f}s (FAIL)")
            # Print last 20 lines of output on failure
            failure_lines = [l for l in output.split("\n") if l.strip()]
            print("\n".join(failure_lines[-20:]))

    # Summary
    print("\n" + "=" * 70)
    print("  测试结果汇总")
    print("=" * 70)
    total = len(results)
    passed = sum(1 for _, p, _, _ in results if p)
    failed = total - passed
    total_time = sum(e for _, _, e, _ in results)

    for tf, p, elapsed, _ in results:
        status = "✅" if p else "❌"
        print(f"  {status} {tf:45s} {elapsed:.1f}s")

    print(f"\n  总计: {total} 文件 | 通过: {passed} | 失败: {failed} | 耗时: {total_time:.1f}s")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
