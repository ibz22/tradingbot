"""
Comprehensive Token Validation Testing Suite
==========================================

Advanced testing suite for Phase 3 Session 3 token validation system including:
- Token validation accuracy testing with known good/bad tokens
- Integration testing between all validation components  
- Performance benchmarking and stress testing
- Real-world scenario validation and edge case handling
- Component reliability and error recovery testing
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import statistics

# Test framework imports
import pytest
import unittest
from unittest.mock import Mock, patch

# Import validation system components
try:
    from solana_trading.discovery.token_validator import (
        TokenValidator, ValidationStatus, RiskLevel, TokenMetadata, 
        HolderAnalysis, SecurityAnalysis, ValidationResult
    )
    from solana_trading.discovery.liquidity_analyzer import (
        LiquidityAnalyzer, LiquidityMetrics, LiquidityTier, TradeFeasibility,
        LiquidityPool, TradingRecommendation
    )
    from solana_trading.discovery.rug_detector import (
        RugPullDetector, RugPullAnalysis, DetectionStatus, 
        TradingPattern, LiquidityRisk, DeveloperAnalysis
    )
    from solana_trading.discovery.token_extractor import (
        TokenExtractor, ExtractedToken, ValidatedToken
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure all validation components are properly installed")


@dataclass
class TestCase:
    """Test case definition"""
    name: str
    token_address: str
    expected_status: str
    expected_risk_level: str
    description: str
    test_type: str  # 'positive', 'negative', 'edge_case'
    expected_warnings: List[str] = None
    timeout_seconds: int = 30
    
    def __post_init__(self):
        if self.expected_warnings is None:
            self.expected_warnings = []


@dataclass
class TestResult:
    """Test result data"""
    test_case: TestCase
    passed: bool
    actual_status: Optional[str] = None
    actual_risk_level: Optional[str] = None
    execution_time_ms: float = 0.0
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = None
    validation_details: Optional[Dict] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
        if self.validation_details is None:
            self.validation_details = {}


@dataclass  
class TestSuiteResults:
    """Complete test suite results"""
    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    accuracy_percentage: float = 0.0
    average_execution_time: float = 0.0
    component_results: Dict[str, Dict] = None
    performance_metrics: Dict[str, float] = None
    detailed_results: List[TestResult] = None
    
    def __post_init__(self):
        if self.component_results is None:
            self.component_results = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.detailed_results is None:
            self.detailed_results = []


class TokenValidationTestSuite:
    """
    Comprehensive test suite for token validation system
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Test cases for different scenarios
        self.test_cases = self._define_test_cases()
        
        # Component instances for testing
        self.token_validator = None
        self.liquidity_analyzer = None 
        self.rug_detector = None
        self.token_extractor = None
        
        # Test results storage
        self.results = TestSuiteResults()
    
    def _define_test_cases(self) -> List[TestCase]:
        """Define comprehensive test cases"""
        
        # Known good tokens (legitimate Solana ecosystem tokens)
        good_tokens = [
            TestCase(
                name="SOL_Native_Token",
                token_address="So11111111111111111111111111111111111111112",
                expected_status="verified",
                expected_risk_level="VERY_LOW",
                description="Native SOL token - should be verified with very low risk",
                test_type="positive"
            ),
            TestCase(
                name="USDC_Stablecoin",
                token_address="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", 
                expected_status="verified",
                expected_risk_level="VERY_LOW",
                description="USDC stablecoin - established, high liquidity",
                test_type="positive"
            ),
            TestCase(
                name="USDT_Stablecoin", 
                token_address="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
                expected_status="verified",
                expected_risk_level="LOW",
                description="USDT stablecoin - established token",
                test_type="positive"
            )
        ]
        
        # Suspicious tokens (tokens with some risk factors)
        suspicious_tokens = [
            TestCase(
                name="High_Concentration_Token",
                token_address="DemoToken1111111111111111111111111111111111",
                expected_status="suspicious", 
                expected_risk_level="HIGH",
                description="Token with concentrated holder distribution",
                test_type="negative",
                expected_warnings=["High concentration detected"]
            ),
            TestCase(
                name="Mint_Authority_Token",
                token_address="DemoToken2222222222222222222222222222222222",
                expected_status="suspicious",
                expected_risk_level="MODERATE", 
                description="Token with active mint authority",
                test_type="negative",
                expected_warnings=["Active mint authority detected"]
            )
        ]
        
        # Invalid tokens (clear scams/rugs)
        invalid_tokens = [
            TestCase(
                name="Known_Rug_Pull",
                token_address="RugToken1111111111111111111111111111111111",
                expected_status="invalid",
                expected_risk_level="VERY_HIGH",
                description="Known rug pull token",
                test_type="negative",
                expected_warnings=["Rug pull detected"]
            )
        ]
        
        # Edge cases
        edge_cases = [
            TestCase(
                name="Invalid_Address_Format",
                token_address="InvalidAddress123",
                expected_status="invalid", 
                expected_risk_level="VERY_HIGH",
                description="Invalid Solana address format",
                test_type="edge_case",
                expected_warnings=["Invalid address format"]
            ),
            TestCase(
                name="Empty_Address",
                token_address="",
                expected_status="invalid",
                expected_risk_level="VERY_HIGH", 
                description="Empty token address",
                test_type="edge_case"
            ),
            TestCase(
                name="Non_Existent_Token",
                token_address="11111111111111111111111111111111111111111111",
                expected_status="failed",
                expected_risk_level="VERY_HIGH",
                description="Non-existent token address",
                test_type="edge_case"
            )
        ]
        
        return good_tokens + suspicious_tokens + invalid_tokens + edge_cases
    
    async def setup_components(self, 
                             use_mock_apis: bool = True,
                             solscan_api_key: Optional[str] = None,
                             helius_api_key: Optional[str] = None):
        """
        Setup validation components for testing
        
        Args:
            use_mock_apis: Whether to use mocked API responses
            solscan_api_key: Solscan API key for real API testing
            helius_api_key: Helius API key for real API testing
        """
        self.logger.info("Setting up validation components for testing...")
        
        try:
            # Initialize components with test-specific configurations
            self.token_validator = TokenValidator(
                solscan_api_key=solscan_api_key if not use_mock_apis else None,
                helius_api_key=helius_api_key if not use_mock_apis else None,
                checkpoint_file="data/test_token_validator.json"
            )
            
            self.liquidity_analyzer = LiquidityAnalyzer(
                checkpoint_file="data/test_liquidity_analyzer.json"
            )
            
            self.rug_detector = RugPullDetector(
                checkpoint_file="data/test_rug_detector.json"
            )
            
            self.token_extractor = TokenExtractor(
                token_validator=self.token_validator,
                liquidity_analyzer=self.liquidity_analyzer,
                rug_detector=self.rug_detector,
                checkpoint_file="data/test_token_extractor.json"
            )
            
            if use_mock_apis:
                await self._setup_mock_apis()
            
            self.logger.info("Validation components setup complete")
            
        except Exception as e:
            self.logger.error(f"Error setting up components: {e}")
            raise
    
    async def _setup_mock_apis(self):
        """Setup mock API responses for testing"""
        
        # Mock successful validation responses
        mock_metadata_responses = {
            "So11111111111111111111111111111111111111112": {  # SOL
                "success": True,
                "data": {
                    "name": "Wrapped SOL",
                    "symbol": "SOL", 
                    "decimals": 9,
                    "supply": 1000000000,
                    "mintAuthority": None,
                    "freezeAuthority": None,
                    "isInitialized": True
                }
            },
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {  # USDC
                "success": True,
                "data": {
                    "name": "USD Coin",
                    "symbol": "USDC",
                    "decimals": 6,
                    "supply": 5000000000,
                    "mintAuthority": None,
                    "freezeAuthority": None,
                    "isInitialized": True
                }
            }
        }
        
        # Mock holder distribution responses
        mock_holder_responses = {
            "So11111111111111111111111111111111111111112": {
                "success": True,
                "total": 1000000,
                "data": [
                    {"address": "holder1", "amount": "100000"},
                    {"address": "holder2", "amount": "80000"},
                    {"address": "holder3", "amount": "60000"}
                ]
            }
        }
        
        # Apply mocks
        if self.token_validator:
            # Mock API methods would go here
            # For now we'll use the real implementations with test data
            pass
    
    async def test_token_validator_accuracy(self) -> Dict[str, Any]:
        """Test token validator accuracy against known test cases"""
        
        self.logger.info("Testing TokenValidator accuracy...")
        
        results = {
            "component": "TokenValidator",
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_results": []
        }
        
        if not self.token_validator:
            self.logger.error("TokenValidator not initialized")
            return results
        
        for test_case in self.test_cases:
            try:
                start_time = time.time()
                
                # Run validation
                validation_result = await self.token_validator.validate_token(
                    test_case.token_address
                )
                
                execution_time = (time.time() - start_time) * 1000
                
                # Check results
                passed = (
                    validation_result.status.value == test_case.expected_status and
                    validation_result.risk_level.name == test_case.expected_risk_level
                )
                
                test_result = TestResult(
                    test_case=test_case,
                    passed=passed,
                    actual_status=validation_result.status.value,
                    actual_risk_level=validation_result.risk_level.name,
                    execution_time_ms=execution_time,
                    confidence_score=validation_result.confidence,
                    validation_details={
                        "metadata_available": validation_result.metadata is not None,
                        "holder_analysis_available": validation_result.holder_analysis is not None,
                        "security_analysis_available": validation_result.security_analysis is not None,
                        "validation_errors": validation_result.validation_errors,
                        "validation_warnings": validation_result.validation_warnings
                    }
                )
                
                results["test_results"].append(asdict(test_result))
                results["total_tests"] += 1
                
                if passed:
                    results["passed_tests"] += 1
                    self.logger.info(f"✅ {test_case.name}: PASSED")
                else:
                    results["failed_tests"] += 1
                    self.logger.warning(
                        f"❌ {test_case.name}: FAILED - "
                        f"Expected: {test_case.expected_status}/{test_case.expected_risk_level}, "
                        f"Got: {validation_result.status.value}/{validation_result.risk_level.name}"
                    )
                
            except Exception as e:
                self.logger.error(f"Error testing {test_case.name}: {e}")
                results["failed_tests"] += 1
                results["total_tests"] += 1
                
                test_result = TestResult(
                    test_case=test_case,
                    passed=False,
                    error_message=str(e)
                )
                results["test_results"].append(asdict(test_result))
        
        results["accuracy_percentage"] = (
            results["passed_tests"] / max(results["total_tests"], 1) * 100
        )
        
        self.logger.info(
            f"TokenValidator accuracy: {results['accuracy_percentage']:.1f}% "
            f"({results['passed_tests']}/{results['total_tests']})"
        )
        
        return results
    
    async def test_liquidity_analyzer_performance(self) -> Dict[str, Any]:
        """Test liquidity analyzer performance and accuracy"""
        
        self.logger.info("Testing LiquidityAnalyzer performance...")
        
        results = {
            "component": "LiquidityAnalyzer", 
            "total_tests": 0,
            "performance_metrics": {},
            "test_results": []
        }
        
        if not self.liquidity_analyzer:
            self.logger.error("LiquidityAnalyzer not initialized")
            return results
        
        # Test tokens with known liquidity characteristics
        test_tokens = [
            ("So11111111111111111111111111111111111111112", "very_high"),  # SOL
            ("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v", "very_high"),  # USDC
        ]
        
        execution_times = []
        
        for token_address, expected_tier in test_tokens:
            try:
                start_time = time.time()
                
                # Analyze liquidity
                liquidity_metrics = await self.liquidity_analyzer.analyze_token_liquidity(
                    token_address
                )
                
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
                
                # Generate trading recommendation
                recommendation = self.liquidity_analyzer.generate_trading_recommendation(
                    liquidity_metrics, 1000.0
                )
                
                # Evaluate results
                tier_correct = liquidity_metrics.liquidity_tier.value == expected_tier
                has_pools = len(liquidity_metrics.best_pools) > 0
                has_recommendation = recommendation.feasibility != TradeFeasibility.UNSUITABLE
                
                passed = tier_correct and has_pools
                
                test_result = {
                    "token_address": token_address,
                    "expected_tier": expected_tier,
                    "actual_tier": liquidity_metrics.liquidity_tier.value,
                    "execution_time": execution_time,
                    "passed": passed,
                    "metrics": {
                        "total_liquidity_usd": liquidity_metrics.total_liquidity_usd,
                        "pool_count": liquidity_metrics.pool_count,
                        "stability_score": liquidity_metrics.stability_score,
                        "recommendation_feasibility": recommendation.feasibility.value,
                        "expected_slippage": recommendation.expected_slippage_pct
                    }
                }
                
                results["test_results"].append(test_result)
                results["total_tests"] += 1
                
                if passed:
                    self.logger.info(f"✅ Liquidity analysis for {token_address[:8]}... PASSED")
                else:
                    self.logger.warning(f"❌ Liquidity analysis for {token_address[:8]}... FAILED")
                
            except Exception as e:
                self.logger.error(f"Error analyzing liquidity for {token_address}: {e}")
        
        if execution_times:
            results["performance_metrics"] = {
                "average_execution_time": statistics.mean(execution_times),
                "max_execution_time": max(execution_times),
                "min_execution_time": min(execution_times)
            }
        
        return results
    
    async def test_rug_detector_accuracy(self) -> Dict[str, Any]:
        """Test rug pull detector accuracy"""
        
        self.logger.info("Testing RugPullDetector accuracy...")
        
        results = {
            "component": "RugPullDetector",
            "total_tests": 0,
            "test_results": []
        }
        
        if not self.rug_detector:
            self.logger.error("RugPullDetector not initialized")
            return results
        
        # Test with known good tokens (should be low risk)
        good_tokens = [
            "So11111111111111111111111111111111111111112",  # SOL
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
        ]
        
        for token_address in good_tokens:
            try:
                # Analyze rug pull risk
                rug_analysis = await self.rug_detector.analyze_rug_risk(token_address)
                
                # Good tokens should have low risk
                expected_low_risk = rug_analysis.risk_level.value <= 0.5
                not_flagged_as_rug = rug_analysis.detection_status.value not in ["likely_rug", "confirmed_rug"]
                
                passed = expected_low_risk and not_flagged_as_rug
                
                test_result = {
                    "token_address": token_address,
                    "risk_level": rug_analysis.risk_level.name,
                    "detection_status": rug_analysis.detection_status.value,
                    "overall_risk_score": rug_analysis.overall_risk_score,
                    "confidence": rug_analysis.confidence,
                    "passed": passed
                }
                
                results["test_results"].append(test_result)
                results["total_tests"] += 1
                
                if passed:
                    self.logger.info(f"✅ Rug analysis for {token_address[:8]}... PASSED")
                else:
                    self.logger.warning(f"❌ Rug analysis for {token_address[:8]}... FAILED")
                    
            except Exception as e:
                self.logger.error(f"Error in rug analysis for {token_address}: {e}")
        
        return results
    
    async def test_integration_pipeline(self) -> Dict[str, Any]:
        """Test complete validation pipeline integration"""
        
        self.logger.info("Testing complete validation pipeline integration...")
        
        results = {
            "component": "IntegrationPipeline",
            "total_tests": 0,
            "passed_tests": 0,
            "test_results": []
        }
        
        if not self.token_extractor:
            self.logger.error("TokenExtractor not initialized")
            return results
        
        # Test complete pipeline with sample text
        test_texts = [
            "$SOL surges 20% after major partnership announcement",
            "New DeFi protocol launches on Solana with $USDC rewards",
            "Warning: avoid scam token at address 1nc1nerator11111111111111111111111111111111",
        ]
        
        for i, text in enumerate(test_texts):
            try:
                # Run complete discovery and validation pipeline
                validated_tokens = await self.token_extractor.discover_and_validate_tokens(
                    text=text,
                    source=f"test_source_{i}",
                    validation_enabled=True
                )
                
                # Check if we got results
                has_results = len(validated_tokens) > 0
                has_validation_data = any(
                    token.is_validated and token.final_confidence > 0 
                    for token in validated_tokens
                )
                
                passed = has_results and (not has_validation_data or 
                         any(token.trading_recommendation != "avoid" for token in validated_tokens))
                
                test_result = {
                    "test_text": text[:50] + "...",
                    "tokens_found": len(validated_tokens),
                    "validated_tokens": [
                        {
                            "symbol": token.symbol,
                            "validation_status": token.validation_status,
                            "liquidity_tier": token.liquidity_tier,
                            "rug_risk_level": token.rug_risk_level,
                            "trading_recommendation": token.trading_recommendation,
                            "final_confidence": token.final_confidence
                        }
                        for token in validated_tokens
                    ],
                    "passed": passed
                }
                
                results["test_results"].append(test_result)
                results["total_tests"] += 1
                
                if passed:
                    results["passed_tests"] += 1
                    self.logger.info(f"✅ Pipeline test {i+1}: PASSED ({len(validated_tokens)} tokens)")
                else:
                    self.logger.warning(f"❌ Pipeline test {i+1}: FAILED")
                    
            except Exception as e:
                self.logger.error(f"Error in pipeline test {i+1}: {e}")
                results["total_tests"] += 1
        
        return results
    
    async def test_performance_benchmarks(self) -> Dict[str, Any]:
        """Test performance benchmarks and stress testing"""
        
        self.logger.info("Running performance benchmarks...")
        
        results = {
            "component": "PerformanceBenchmarks",
            "benchmarks": {}
        }
        
        # Benchmark 1: Single token validation speed
        if self.token_validator:
            start_time = time.time()
            try:
                await self.token_validator.validate_token("So11111111111111111111111111111111111111112")
                single_validation_time = time.time() - start_time
                results["benchmarks"]["single_token_validation_seconds"] = single_validation_time
                
                # Performance target: <5 seconds for single validation
                results["benchmarks"]["single_validation_performance"] = "PASS" if single_validation_time < 5.0 else "FAIL"
                
            except Exception as e:
                results["benchmarks"]["single_validation_error"] = str(e)
        
        # Benchmark 2: Batch processing performance  
        test_addresses = [
            "So11111111111111111111111111111111111111112",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        ]
        
        if self.token_validator:
            start_time = time.time()
            try:
                batch_results = await self.token_validator.batch_validate_tokens(test_addresses)
                batch_time = time.time() - start_time
                
                results["benchmarks"]["batch_validation_seconds"] = batch_time
                results["benchmarks"]["batch_tokens_processed"] = len(batch_results)
                results["benchmarks"]["avg_time_per_token"] = batch_time / len(test_addresses)
                
                # Performance target: <10 seconds for 2 tokens  
                results["benchmarks"]["batch_performance"] = "PASS" if batch_time < 10.0 else "FAIL"
                
            except Exception as e:
                results["benchmarks"]["batch_validation_error"] = str(e)
        
        # Benchmark 3: Complete pipeline throughput
        test_text = "$SOL and $USDC showing strong momentum in DeFi sector"
        
        if self.token_extractor:
            start_time = time.time()
            try:
                pipeline_results = await self.token_extractor.discover_and_validate_tokens(
                    text_text, "benchmark_test"
                )
                pipeline_time = time.time() - start_time
                
                results["benchmarks"]["pipeline_processing_seconds"] = pipeline_time
                results["benchmarks"]["pipeline_tokens_processed"] = len(pipeline_results)
                
                # Performance target: <15 seconds for complete pipeline
                results["benchmarks"]["pipeline_performance"] = "PASS" if pipeline_time < 15.0 else "FAIL"
                
            except Exception as e:
                results["benchmarks"]["pipeline_error"] = str(e)
        
        return results
    
    async def run_full_test_suite(self, 
                                use_mock_apis: bool = True,
                                solscan_api_key: Optional[str] = None,
                                helius_api_key: Optional[str] = None) -> TestSuiteResults:
        """
        Run the complete test suite
        
        Args:
            use_mock_apis: Use mock API responses for testing
            solscan_api_key: Solscan API key for real API testing
            helius_api_key: Helius API key for real API testing
            
        Returns:
            Complete test suite results
        """
        self.logger.info("🚀 Starting comprehensive token validation test suite...")
        
        start_time = time.time()
        
        try:
            # Setup components
            await self.setup_components(use_mock_apis, solscan_api_key, helius_api_key)
            
            # Run all test categories
            validator_results = await self.test_token_validator_accuracy()
            liquidity_results = await self.test_liquidity_analyzer_performance()
            rug_results = await self.test_rug_detector_accuracy()
            integration_results = await self.test_integration_pipeline()
            performance_results = await self.test_performance_benchmarks()
            
            # Aggregate results
            total_execution_time = time.time() - start_time
            
            total_tests = sum([
                validator_results.get("total_tests", 0),
                liquidity_results.get("total_tests", 0),
                rug_results.get("total_tests", 0), 
                integration_results.get("total_tests", 0)
            ])
            
            passed_tests = sum([
                validator_results.get("passed_tests", 0),
                0,  # liquidity and rug tests don't have pass/fail counts
                0,
                integration_results.get("passed_tests", 0)
            ])
            
            # Calculate overall accuracy
            accuracy = (passed_tests / max(total_tests, 1)) * 100
            
            # Compile final results
            self.results = TestSuiteResults(
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=total_tests - passed_tests,
                accuracy_percentage=accuracy,
                average_execution_time=total_execution_time / max(total_tests, 1),
                component_results={
                    "token_validator": validator_results,
                    "liquidity_analyzer": liquidity_results,
                    "rug_detector": rug_results,
                    "integration_pipeline": integration_results
                },
                performance_metrics=performance_results.get("benchmarks", {})
            )
            
            # Log summary
            self.logger.info("📊 Test Suite Results Summary:")
            self.logger.info(f"   Total Tests: {total_tests}")
            self.logger.info(f"   Passed: {passed_tests}")
            self.logger.info(f"   Failed: {total_tests - passed_tests}")
            self.logger.info(f"   Accuracy: {accuracy:.1f}%")
            self.logger.info(f"   Total Execution Time: {total_execution_time:.1f}s")
            
            # Component-specific summaries
            self.logger.info(f"   TokenValidator Accuracy: {validator_results.get('accuracy_percentage', 0):.1f}%")
            self.logger.info(f"   Integration Tests Passed: {integration_results.get('passed_tests', 0)}/{integration_results.get('total_tests', 0)}")
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"Error running test suite: {e}")
            raise
        finally:
            # Cleanup
            await self._cleanup_components()
    
    async def _cleanup_components(self):
        """Cleanup test components"""
        try:
            if self.token_validator:
                await self.token_validator.close()
            if self.liquidity_analyzer:
                await self.liquidity_analyzer.close()
            if self.rug_detector:
                await self.rug_detector.close()
        except Exception as e:
            self.logger.warning(f"Error during cleanup: {e}")
    
    def generate_test_report(self, output_file: str = "test_results.json"):
        """Generate comprehensive test report"""
        
        if not self.results:
            self.logger.error("No test results available")
            return
        
        # Create detailed report
        report = {
            "test_suite": "Token Validation System Test Suite",
            "execution_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": self.results.total_tests,
                "passed_tests": self.results.passed_tests,
                "failed_tests": self.results.failed_tests,
                "accuracy_percentage": self.results.accuracy_percentage,
                "average_execution_time_seconds": self.results.average_execution_time
            },
            "component_results": self.results.component_results,
            "performance_benchmarks": self.results.performance_metrics,
            "success_criteria": {
                "target_accuracy": 90.0,
                "accuracy_achieved": self.results.accuracy_percentage,
                "target_met": self.results.accuracy_percentage >= 90.0,
                "performance_targets_met": all(
                    result == "PASS" 
                    for key, result in self.results.performance_metrics.items()
                    if key.endswith("_performance")
                )
            }
        }
        
        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"📄 Test report saved to {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("🧪 TOKEN VALIDATION TEST SUITE RESULTS")
        print("="*60)
        print(f"Total Tests Run: {self.results.total_tests}")
        print(f"Tests Passed: {self.results.passed_tests}")
        print(f"Tests Failed: {self.results.failed_tests}")
        print(f"Overall Accuracy: {self.results.accuracy_percentage:.1f}%")
        print(f"Target Accuracy (90%): {'✅ MET' if self.results.accuracy_percentage >= 90.0 else '❌ NOT MET'}")
        print(f"Average Execution Time: {self.results.average_execution_time:.2f}s")
        
        # Component breakdown
        print(f"\nComponent Results:")
        for component, results in self.results.component_results.items():
            if 'accuracy_percentage' in results:
                print(f"  {component}: {results['accuracy_percentage']:.1f}%")
            elif 'total_tests' in results:
                passed = results.get('passed_tests', 0)
                total = results.get('total_tests', 0)
                print(f"  {component}: {passed}/{total} tests passed")
        
        print("="*60)
        
        return report


# Main test execution
async def main():
    """Run the comprehensive test suite"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run test suite
    test_suite = TokenValidationTestSuite()
    
    try:
        # Run with mock APIs for faster testing
        results = await test_suite.run_full_test_suite(use_mock_apis=True)
        
        # Generate report
        test_suite.generate_test_report("data/token_validation_test_results.json")
        
        # Return results for programmatic use
        return results
        
    except Exception as e:
        logging.error(f"Test suite execution failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())