"""Unit tests for SQL recommendation generator."""

import pytest
from analysis.sql_analyzer import SQLRecommendationGenerator, SQLRecommendation
from core.models import SQLQuery


class TestSQLRecommendationGenerator:
    """Test suite for SQLRecommendationGenerator."""
    
    @pytest.fixture
    def generator(self):
        """Create a SQLRecommendationGenerator instance."""
        return SQLRecommendationGenerator()
    
    def test_generator_initialization(self, generator):
        """Test generator initialization with default thresholds."""
        assert generator.index_efficiency_threshold == 0.1
        assert generator.lock_time_threshold_pct == 30.0
        assert generator.cpu_time_threshold_pct == 80.0
        assert generator.high_frequency_threshold == 1.0
        assert generator.high_execution_time_threshold == 1000.0
    
    def test_generator_custom_thresholds(self):
        """Test generator initialization with custom thresholds."""
        generator = SQLRecommendationGenerator(
            index_efficiency_threshold=0.05,
            lock_time_threshold_pct=20.0,
            cpu_time_threshold_pct=70.0,
            high_frequency_threshold=2.0,
            high_execution_time_threshold=500.0
        )
        
        assert generator.index_efficiency_threshold == 0.05
        assert generator.lock_time_threshold_pct == 20.0
        assert generator.cpu_time_threshold_pct == 70.0
        assert generator.high_frequency_threshold == 2.0
        assert generator.high_execution_time_threshold == 500.0
    
    def test_calculate_efficiency_ratio_normal(self, generator):
        """Test efficiency ratio calculation with normal values."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='SELECT * FROM users',
            total_execution_time=100.0,
            average_execution_time=10.0,
            execution_count=10,
            rows_examined=1000,
            rows_returned=100
        )
        
        ratio = generator._calculate_efficiency_ratio(query)
        assert ratio == 0.1  # 100 / 1000
    
    def test_calculate_efficiency_ratio_perfect(self, generator):
        """Test efficiency ratio with perfect selectivity."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='SELECT * FROM users WHERE id = 1',
            total_execution_time=10.0,
            average_execution_time=10.0,
            execution_count=1,
            rows_examined=1,
            rows_returned=1
        )
        
        ratio = generator._calculate_efficiency_ratio(query)
        assert ratio == 1.0
    
    def test_calculate_efficiency_ratio_missing_metrics(self, generator):
        """Test efficiency ratio with missing metrics."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='SELECT * FROM users',
            total_execution_time=100.0,
            average_execution_time=10.0,
            execution_count=10,
            rows_examined=None,  # Missing
            rows_returned=100
        )
        
        ratio = generator._calculate_efficiency_ratio(query)
        assert ratio is None
    
    def test_calculate_efficiency_ratio_zero_examined(self, generator):
        """Test efficiency ratio with zero rows examined."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='SELECT * FROM users',
            total_execution_time=10.0,
            average_execution_time=10.0,
            execution_count=1,
            rows_examined=0,
            rows_returned=0
        )
        
        ratio = generator._calculate_efficiency_ratio(query)
        assert ratio is None
    
    def test_calculate_lock_time_percentage(self, generator):
        """Test lock time percentage calculation."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='UPDATE users SET status = ?',
            total_execution_time=100.0,
            average_execution_time=100.0,
            execution_count=1,
            lock_time=40.0
        )
        
        pct = generator._calculate_lock_time_percentage(query)
        assert pct == 40.0  # 40 / 100 * 100
    
    def test_calculate_lock_time_percentage_missing_metrics(self, generator):
        """Test lock time percentage with missing metrics."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='UPDATE users',
            total_execution_time=100.0,
            average_execution_time=100.0,
            execution_count=1,
            lock_time=None
        )
        
        pct = generator._calculate_lock_time_percentage(query)
        assert pct is None
    
    def test_calculate_cpu_time_percentage(self, generator):
        """Test CPU time percentage calculation."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='SELECT * FROM users',
            total_execution_time=100.0,
            average_execution_time=100.0,
            execution_count=1,
            cpu_time=85.0
        )
        
        pct = generator._calculate_cpu_time_percentage(query)
        assert pct == 85.0  # 85 / 100 * 100
    
    def test_identify_index_opportunity_critical(self, generator):
        """Test identification of critical index opportunity."""
        query = SQLQuery(
            query_id='sql-1',
            query_text='SELECT * FROM users WHERE email LIKE "%@example.com"',
            total_execution_time=5000.0,  # High execution time
            average_execution_time=50.0,
            execution_count=100,
            rows_examined=100000,
            rows_returned=50  # Very low efficiency (0.05%)
        )
        
        recommendations = generator._identify_index_opportunities([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.query_id == 'sql-1'
        assert rec.severity == 'critical'
        assert rec.category == 'index'
        assert 'index' in rec.recommendation.lower()
        assert rec.metrics['efficiency_ratio'] == 0.0005
    
    def test_identify_index_opportunity_warning(self, generator):
        """Test identification of warning-level index opportunity."""
        query = SQLQuery(
            query_id='sql-2',
            query_text='SELECT * FROM orders WHERE status = ?',
            total_execution_time=500.0,  # Below critical threshold
            average_execution_time=5.0,
            execution_count=150,  # High frequency
            rows_examined=10000,
            rows_returned=100  # Low efficiency (1%)
        )
        
        recommendations = generator._identify_index_opportunities([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.severity == 'warning'
        assert rec.category == 'index'
    
    def test_identify_index_opportunity_info(self, generator):
        """Test identification of info-level index opportunity."""
        query = SQLQuery(
            query_id='sql-3',
            query_text='SELECT * FROM products',
            total_execution_time=200.0,  # Low execution time
            average_execution_time=20.0,
            execution_count=10,  # Low frequency
            rows_examined=1000,
            rows_returned=10  # Low efficiency (1%)
        )
        
        recommendations = generator._identify_index_opportunities([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.severity == 'info'
    
    def test_identify_index_opportunity_no_issue(self, generator):
        """Test that efficient queries don't generate recommendations."""
        query = SQLQuery(
            query_id='sql-4',
            query_text='SELECT * FROM users WHERE id = ?',
            total_execution_time=10.0,
            average_execution_time=10.0,
            execution_count=1,
            rows_examined=1,
            rows_returned=1  # Perfect efficiency (100%)
        )
        
        recommendations = generator._identify_index_opportunities([query])
        assert len(recommendations) == 0
    
    def test_detect_lock_contention_critical(self, generator):
        """Test detection of critical lock contention."""
        query = SQLQuery(
            query_id='sql-5',
            query_text='UPDATE inventory SET quantity = ?',
            total_execution_time=100.0,
            average_execution_time=100.0,
            execution_count=50,
            lock_time=60.0  # 60% lock time
        )
        
        recommendations = generator._detect_lock_contention([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.query_id == 'sql-5'
        assert rec.severity == 'critical'
        assert rec.category == 'lock'
        assert 'lock' in rec.recommendation.lower()
        assert rec.metrics['lock_time_percentage'] == 60.0
    
    def test_detect_lock_contention_warning(self, generator):
        """Test detection of warning-level lock contention."""
        query = SQLQuery(
            query_id='sql-6',
            query_text='UPDATE orders SET status = ?',
            total_execution_time=100.0,
            average_execution_time=100.0,
            execution_count=150,  # High frequency
            lock_time=35.0  # 35% lock time
        )
        
        recommendations = generator._detect_lock_contention([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.severity == 'warning'
    
    def test_detect_lock_contention_no_issue(self, generator):
        """Test that queries with low lock time don't generate recommendations."""
        query = SQLQuery(
            query_id='sql-7',
            query_text='SELECT * FROM users',
            total_execution_time=100.0,
            average_execution_time=100.0,
            execution_count=10,
            lock_time=5.0  # Only 5% lock time
        )
        
        recommendations = generator._detect_lock_contention([query])
        assert len(recommendations) == 0
    
    def test_suggest_caching_high_frequency(self, generator):
        """Test caching suggestion for high-frequency query."""
        query = SQLQuery(
            query_id='sql-8',
            query_text='SELECT * FROM config WHERE key = ?',
            total_execution_time=500.0,
            average_execution_time=5.0,  # Fast query
            execution_count=100,
            executions_per_second=15.0  # Very high frequency
        )
        
        recommendations = generator._suggest_caching_candidates([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.query_id == 'sql-8'
        assert rec.severity == 'warning'
        assert rec.category == 'cache'
        assert 'cach' in rec.recommendation.lower()
    
    def test_suggest_caching_high_execution_count(self, generator):
        """Test caching suggestion based on execution count."""
        query = SQLQuery(
            query_id='sql-9',
            query_text='SELECT name FROM categories',
            total_execution_time=5000.0,
            average_execution_time=10.0,  # Fast query
            execution_count=6000,  # Very high count
            executions_per_second=None
        )
        
        recommendations = generator._suggest_caching_candidates([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.category == 'cache'
    
    def test_suggest_caching_not_for_slow_queries(self, generator):
        """Test that slow queries are not suggested for caching."""
        query = SQLQuery(
            query_id='sql-10',
            query_text='SELECT * FROM large_table',
            total_execution_time=5000.0,
            average_execution_time=500.0,  # Slow query
            execution_count=10,
            executions_per_second=2.0  # High frequency
        )
        
        recommendations = generator._suggest_caching_candidates([query])
        assert len(recommendations) == 0
    
    def test_suggest_caching_only_for_select(self, generator):
        """Test that only SELECT queries are suggested for caching."""
        query_update = SQLQuery(
            query_id='sql-11',
            query_text='UPDATE users SET last_login = NOW()',
            total_execution_time=500.0,
            average_execution_time=5.0,
            execution_count=100,
            executions_per_second=2.0
        )
        
        recommendations = generator._suggest_caching_candidates([query_update])
        assert len(recommendations) == 0
    
    def test_identify_cpu_intensive_critical(self, generator):
        """Test identification of critical CPU-intensive query."""
        query = SQLQuery(
            query_id='sql-12',
            query_text='SELECT * FROM users WHERE UPPER(email) LIKE ?',
            total_execution_time=6000.0,
            average_execution_time=600.0,
            execution_count=10,
            cpu_time=5500.0  # 91.7% CPU time, > 5 seconds
        )
        
        recommendations = generator._identify_cpu_intensive([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.query_id == 'sql-12'
        assert rec.severity == 'critical'
        assert rec.category == 'cpu'
        assert 'cpu' in rec.recommendation.lower()
        assert rec.metrics['cpu_time_percentage'] > 80
    
    def test_identify_cpu_intensive_warning(self, generator):
        """Test identification of warning-level CPU-intensive query."""
        query = SQLQuery(
            query_id='sql-13',
            query_text='SELECT COUNT(*) FROM orders GROUP BY date',
            total_execution_time=1200.0,
            average_execution_time=120.0,
            execution_count=10,
            cpu_time=1100.0  # 91.7% CPU time, > 1 second
        )
        
        recommendations = generator._identify_cpu_intensive([query])
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.severity == 'warning'
    
    def test_identify_cpu_intensive_no_issue(self, generator):
        """Test that queries with normal CPU usage don't generate recommendations."""
        query = SQLQuery(
            query_id='sql-14',
            query_text='SELECT * FROM users WHERE id = ?',
            total_execution_time=100.0,
            average_execution_time=100.0,
            execution_count=1,
            cpu_time=50.0  # Only 50% CPU time
        )
        
        recommendations = generator._identify_cpu_intensive([query])
        assert len(recommendations) == 0
    
    def test_generate_recommendations_prioritization(self, generator):
        """Test that recommendations are prioritized by total execution time."""
        query1 = SQLQuery(
            query_id='sql-low',
            query_text='SELECT * FROM small_table',
            total_execution_time=100.0,
            average_execution_time=10.0,
            execution_count=10,
            rows_examined=1000,
            rows_returned=10
        )
        
        query2 = SQLQuery(
            query_id='sql-high',
            query_text='SELECT * FROM large_table',
            total_execution_time=5000.0,  # Much higher
            average_execution_time=50.0,
            execution_count=100,
            rows_examined=100000,
            rows_returned=100
        )
        
        query3 = SQLQuery(
            query_id='sql-medium',
            query_text='SELECT * FROM medium_table',
            total_execution_time=1000.0,
            average_execution_time=20.0,
            execution_count=50,
            rows_examined=10000,
            rows_returned=50
        )
        
        recommendations = generator.generate_recommendations([query1, query2, query3])
        
        # Should be sorted by total_execution_time (highest first)
        assert len(recommendations) == 3
        assert recommendations[0].query_id == 'sql-high'
        assert recommendations[1].query_id == 'sql-medium'
        assert recommendations[2].query_id == 'sql-low'
    
    def test_generate_recommendations_multiple_categories(self, generator):
        """Test generation of recommendations across multiple categories."""
        query = SQLQuery(
            query_id='sql-multi',
            query_text='SELECT * FROM users WHERE email LIKE ?',
            total_execution_time=5000.0,
            average_execution_time=50.0,
            execution_count=100,
            rows_examined=100000,
            rows_returned=50,  # Low efficiency -> index recommendation
            cpu_time=4500.0,  # High CPU -> CPU recommendation
            lock_time=2000.0  # High lock time -> lock recommendation
        )
        
        recommendations = generator.generate_recommendations([query])
        
        # Should generate multiple recommendations for the same query
        assert len(recommendations) >= 2  # At least index and CPU
        categories = {rec.category for rec in recommendations}
        assert 'index' in categories
        assert 'cpu' in categories
    
    def test_generate_recommendations_empty_list(self, generator):
        """Test generation with empty query list."""
        recommendations = generator.generate_recommendations([])
        assert recommendations == []
    
    def test_generate_recommendations_no_enhanced_metrics(self, generator):
        """Test generation with queries lacking enhanced metrics."""
        query = SQLQuery(
            query_id='sql-basic',
            query_text='SELECT * FROM users',
            total_execution_time=100.0,
            average_execution_time=10.0,
            execution_count=10
            # No enhanced metrics
        )
        
        recommendations = generator.generate_recommendations([query])
        # Should not crash, may return empty list or basic recommendations
        assert isinstance(recommendations, list)
    
    def test_property_24_calculation_isolation(self, generator):
        """
        Property 24: Calculation Isolation
        
        For any SQLQuery data model instance, the model SHALL NOT contain
        any calculated fields, with all calculations performed only in
        the recommendation generator.
        """
        query = SQLQuery(
            query_id='sql-test',
            query_text='SELECT * FROM users',
            total_execution_time=100.0,
            average_execution_time=10.0,
            execution_count=10,
            rows_examined=1000,
            rows_returned=100,
            cpu_time=80.0,
            lock_time=30.0
        )
        
        # Verify query object has no calculated fields
        assert not hasattr(query, 'efficiency_ratio')
        assert not hasattr(query, 'lock_time_percentage')
        assert not hasattr(query, 'cpu_time_percentage')
        
        # Generate recommendations (calculations happen here)
        recommendations = generator.generate_recommendations([query])
        
        # Verify query object still has no calculated fields
        assert not hasattr(query, 'efficiency_ratio')
        assert not hasattr(query, 'lock_time_percentage')
        assert not hasattr(query, 'cpu_time_percentage')
        
        # Verify calculations are in recommendations
        if recommendations:
            for rec in recommendations:
                assert 'metrics' in rec.__dict__
                # Metrics dict may contain calculated values
    
    def test_property_25_recommendation_prioritization(self, generator):
        """
        Property 25: Recommendation Prioritization
        
        For any list of recommendations, they SHALL be ordered by potential
        impact, with queries having highest total_execution_time prioritized first.
        """
        queries = [
            SQLQuery(
                query_id=f'sql-{i}',
                query_text=f'SELECT * FROM table{i}',
                total_execution_time=float(i * 100),
                average_execution_time=10.0,
                execution_count=10,
                rows_examined=1000,
                rows_returned=10
            )
            for i in range(1, 11)
        ]
        
        recommendations = generator.generate_recommendations(queries)
        
        # Verify recommendations are sorted by total_execution_time (descending)
        for i in range(len(recommendations) - 1):
            current_time = recommendations[i].metrics.get('total_execution_time', 0)
            next_time = recommendations[i + 1].metrics.get('total_execution_time', 0)
            assert current_time >= next_time
