# -*- coding: utf-8 -*-
"""
Test script for timeout mechanisms and logging improvements
Script kiểm tra cơ chế timeout và cải tiến logging
"""

import asyncio
import time
from logger import logger, DownloadLogger
from retry_utils import async_retry, RetryConfig
from config_manager import ConfigManager

async def test_logging_system():
    """Test the enhanced logging system"""
    print("=== Testing Logging System ===")
    
    # Test basic logging
    logger.info("Testing basic logging functionality")
    logger.warning("This is a warning message", "TEST")
    logger.error("This is an error message", "TEST")
    logger.debug("This is a debug message", "TEST")
    
    # Test progress tracking
    logger.start_chapter_download(1, 5)
    await asyncio.sleep(1)
    logger.complete_chapter_download(1, True, 1500)
    
    logger.start_chapter_download(2, 5)
    await asyncio.sleep(0.5)
    logger.complete_chapter_download(2, False)
    
    # Test operation logging
    logger.log_operation_start("test_operation", "TEST")
    await asyncio.sleep(0.5)
    logger.log_operation_complete("test_operation", 0.5, "TEST")
    
    # Test timeout logging
    logger.log_timeout("test_timeout", 30.0, "TEST")
    
    # Test retry logging
    logger.log_retry("test_retry", 2, 3, 2.0, "TEST")
    
    print("✅ Logging system test completed")

async def test_retry_mechanism():
    """Test the retry mechanism with exponential backoff"""
    print("\n=== Testing Retry Mechanism ===")
    
    # Test successful operation (no retry needed)
    async def success_operation():
        logger.info("Operation succeeded on first try")
        return "success"
    
    result = await async_retry(
        success_operation,
        operation_type='default',
        context='TEST_SUCCESS'
    )
    print(f"Success result: {result}")
    
    # Test operation that fails then succeeds
    attempt_count = 0
    async def fail_then_succeed():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise Exception(f"Simulated failure on attempt {attempt_count}")
        logger.info("Operation succeeded after retry")
        return f"success_after_{attempt_count}_attempts"
    
    attempt_count = 0  # Reset counter
    result = await async_retry(
        fail_then_succeed,
        operation_type='default',
        context='TEST_RETRY'
    )
    print(f"Retry result: {result}")
    
    # Test operation that always fails
    async def always_fail():
        raise Exception("This operation always fails")
    
    try:
        await async_retry(
            always_fail,
            operation_type='default',
            config=RetryConfig(max_attempts=2, base_delay=0.1),
            context='TEST_FAIL'
        )
    except Exception as e:
        print(f"Expected failure: {e}")
    
    print("✅ Retry mechanism test completed")

async def test_timeout_configuration():
    """Test timeout configuration loading"""
    print("\n=== Testing Timeout Configuration ===")
    
    config = ConfigManager()
    timeout_settings = config.get_timeout_settings()
    
    print("Timeout settings:")
    for key, value in timeout_settings.items():
        print(f"  {key}: {value}s")
    
    # Test that timeouts are reasonable
    assert timeout_settings['page_load_timeout'] > 0, "Page load timeout should be positive"
    assert timeout_settings['element_wait_timeout'] > 0, "Element wait timeout should be positive"
    assert timeout_settings['image_download_timeout'] > 0, "Image download timeout should be positive"
    assert timeout_settings['overall_chapter_timeout'] > 0, "Overall chapter timeout should be positive"
    
    print("✅ Timeout configuration test completed")

async def test_timeout_simulation():
    """Test timeout handling with simulated operations"""
    print("\n=== Testing Timeout Simulation ===")
    
    # Test operation that times out
    async def slow_operation():
        logger.info("Starting slow operation...")
        await asyncio.sleep(2)  # Simulate slow operation
        return "completed"
    
    try:
        # Set a short timeout to test timeout handling
        result = await asyncio.wait_for(slow_operation(), timeout=1.0)
        print(f"Unexpected success: {result}")
    except asyncio.TimeoutError:
        logger.log_timeout("slow_operation", 1.0, "TEST_TIMEOUT")
        print("✅ Timeout handled correctly")
    
    # Test operation that completes within timeout
    async def fast_operation():
        logger.info("Starting fast operation...")
        await asyncio.sleep(0.1)  # Fast operation
        return "completed_fast"
    
    try:
        result = await asyncio.wait_for(fast_operation(), timeout=1.0)
        print(f"Fast operation result: {result}")
    except asyncio.TimeoutError:
        print("❌ Unexpected timeout on fast operation")
    
    print("✅ Timeout simulation test completed")

async def main():
    """Run all tests"""
    print("🧪 Starting timeout and logging tests...\n")
    
    try:
        await test_logging_system()
        await test_retry_mechanism()
        await test_timeout_configuration()
        await test_timeout_simulation()
        
        print("\n🎉 All tests completed successfully!")
        print("\n📊 Test Summary:")
        print("  ✅ Logging system - Working")
        print("  ✅ Retry mechanism - Working")
        print("  ✅ Timeout configuration - Working")
        print("  ✅ Timeout simulation - Working")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"\n❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
