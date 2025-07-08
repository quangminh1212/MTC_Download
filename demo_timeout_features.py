# -*- coding: utf-8 -*-
"""
Demo script to showcase timeout mechanisms and logging improvements
Script demo để trình diễn cơ chế timeout và cải tiến logging
"""

import asyncio
import time
from logger import logger
from retry_utils import async_retry, RetryConfig
from config_manager import ConfigManager
from main_config import get_selenium_driver

async def demo_logging_features():
    """Demonstrate the enhanced logging features"""
    print("\n" + "="*60)
    print("🎯 DEMO: Enhanced Logging System")
    print("="*60)
    
    # Show different log levels with timestamps and colors
    logger.info("Starting logging demonstration")
    logger.warning("This is a warning message with context", "DEMO")
    logger.error("This is an error message", "DEMO")
    logger.debug("This is a debug message (may not show in console)", "DEMO")
    
    # Demonstrate progress tracking
    print("\n📊 Progress Tracking Demo:")
    for i in range(1, 4):
        logger.start_chapter_download(i, 3)
        await asyncio.sleep(0.5)  # Simulate work
        logger.complete_chapter_download(i, True, 1200 + i*100)
    
    # Demonstrate operation logging
    print("\n⚙️ Operation Logging Demo:")
    logger.log_operation_start("demo_operation", "DEMO")
    await asyncio.sleep(1)
    logger.log_operation_complete("demo_operation", 1.0, "DEMO")
    
    print("✅ Logging demonstration completed")

async def demo_retry_mechanism():
    """Demonstrate the retry mechanism with exponential backoff"""
    print("\n" + "="*60)
    print("🔄 DEMO: Retry Mechanism with Exponential Backoff")
    print("="*60)
    
    # Demo 1: Operation that succeeds immediately
    print("\n1️⃣ Operation that succeeds immediately:")
    async def immediate_success():
        logger.info("Operation succeeded on first try")
        return "success"
    
    result = await async_retry(
        immediate_success,
        operation_type='default',
        context='DEMO_SUCCESS'
    )
    print(f"   Result: {result}")
    
    # Demo 2: Operation that fails once then succeeds
    print("\n2️⃣ Operation that fails once then succeeds:")
    attempt_counter = 0
    async def fail_then_succeed():
        nonlocal attempt_counter
        attempt_counter += 1
        if attempt_counter == 1:
            raise Exception("Simulated network error")
        logger.info("Operation succeeded after retry")
        return "success_after_retry"
    
    attempt_counter = 0
    result = await async_retry(
        fail_then_succeed,
        operation_type='network_request',
        context='DEMO_RETRY'
    )
    print(f"   Result: {result}")
    
    # Demo 3: Operation with custom retry config
    print("\n3️⃣ Operation with custom retry configuration:")
    custom_config = RetryConfig(
        max_attempts=2,
        base_delay=0.5,
        max_delay=2.0
    )
    
    attempt_counter = 0
    async def custom_retry_demo():
        nonlocal attempt_counter
        attempt_counter += 1
        if attempt_counter < 2:
            raise Exception(f"Attempt {attempt_counter} failed")
        return "custom_success"
    
    attempt_counter = 0
    result = await async_retry(
        custom_retry_demo,
        config=custom_config,
        context='DEMO_CUSTOM'
    )
    print(f"   Result: {result}")
    
    print("✅ Retry mechanism demonstration completed")

async def demo_timeout_handling():
    """Demonstrate timeout handling capabilities"""
    print("\n" + "="*60)
    print("⏱️ DEMO: Timeout Handling")
    print("="*60)
    
    # Demo 1: Operation that completes within timeout
    print("\n1️⃣ Fast operation (completes within timeout):")
    async def fast_operation():
        logger.info("Starting fast operation...")
        await asyncio.sleep(0.5)
        return "fast_completed"
    
    try:
        result = await asyncio.wait_for(fast_operation(), timeout=2.0)
        logger.info(f"Fast operation result: {result}", "DEMO_TIMEOUT")
    except asyncio.TimeoutError:
        logger.log_timeout("fast_operation", 2.0, "DEMO_TIMEOUT")
    
    # Demo 2: Operation that times out
    print("\n2️⃣ Slow operation (times out):")
    async def slow_operation():
        logger.info("Starting slow operation...")
        await asyncio.sleep(3.0)  # This will timeout
        return "slow_completed"
    
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=1.0)
        logger.info(f"Slow operation result: {result}", "DEMO_TIMEOUT")
    except asyncio.TimeoutError:
        logger.log_timeout("slow_operation", 1.0, "DEMO_TIMEOUT")
        logger.warning("Operation timed out as expected", "DEMO_TIMEOUT")
    
    print("✅ Timeout handling demonstration completed")

def demo_configuration():
    """Demonstrate the enhanced configuration system"""
    print("\n" + "="*60)
    print("⚙️ DEMO: Enhanced Configuration System")
    print("="*60)
    
    config = ConfigManager()
    
    # Show timeout settings
    timeout_settings = config.get_timeout_settings()
    print("\n📋 Current Timeout Settings:")
    for key, value in timeout_settings.items():
        print(f"   {key}: {value}s")
    
    # Show app settings
    app_settings = config.get_app_settings()
    print("\n📋 Application Settings:")
    relevant_settings = ['headless', 'retry_attempts', 'enable_detailed_logging', 'log_file']
    for key in relevant_settings:
        if key in app_settings:
            print(f"   {key}: {app_settings[key]}")
    
    print("✅ Configuration demonstration completed")

def demo_selenium_with_timeouts():
    """Demonstrate Selenium driver with timeout configuration"""
    print("\n" + "="*60)
    print("🌐 DEMO: Selenium Driver with Timeout Configuration")
    print("="*60)
    
    try:
        logger.info("Creating Selenium driver with configured timeouts...")
        driver = get_selenium_driver()
        
        # Show that driver was created with proper timeouts
        logger.info("Driver created successfully with timeout settings", "SELENIUM_DEMO")
        
        # Test a simple page load (to a fast-loading page)
        logger.info("Testing page load with timeout...", "SELENIUM_DEMO")
        start_time = time.time()
        
        try:
            driver.get("https://httpbin.org/delay/1")  # Simple test page with 1s delay
            load_time = time.time() - start_time
            logger.info(f"Page loaded successfully in {load_time:.2f}s", "SELENIUM_DEMO")
        except Exception as e:
            logger.warning(f"Page load failed: {e}", "SELENIUM_DEMO")
        
        # Clean up
        driver.quit()
        logger.info("Driver closed successfully", "SELENIUM_DEMO")
        
    except Exception as e:
        logger.error(f"Selenium demo failed: {e}", "SELENIUM_DEMO")
    
    print("✅ Selenium demonstration completed")

async def main():
    """Run all demonstrations"""
    print("🎉 MeTruyenCV Downloader - Timeout & Logging Features Demo")
    print("🕐 Demonstrating comprehensive timeout mechanisms and enhanced logging")
    
    try:
        # Run all demos
        await demo_logging_features()
        await demo_retry_mechanism()
        await demo_timeout_handling()
        demo_configuration()
        demo_selenium_with_timeouts()
        
        print("\n" + "="*60)
        print("🎊 ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📋 Summary of Features Demonstrated:")
        print("   ✅ Enhanced logging with timestamps and colors")
        print("   ✅ Progress tracking for downloads")
        print("   ✅ Retry mechanism with exponential backoff")
        print("   ✅ Timeout handling for operations")
        print("   ✅ Configurable timeout settings")
        print("   ✅ Selenium driver with timeout configuration")
        
        print("\n🚀 The MeTruyenCV downloader now has comprehensive")
        print("   timeout protection and detailed logging capabilities!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
