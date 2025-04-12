# Vector Search Performance Benchmarks

This directory contains performance benchmark tests for the vector search functionality in the Uno framework.

## Running the Benchmarks

To run the benchmarks, use the following command:

```bash
hatch run test:benchmark
```

Or manually with pytest:

```bash
pytest tests/benchmarks --run-benchmark
```

To run only vector search benchmarks:

```bash
pytest tests/benchmarks/test_vector_search_performance.py --run-benchmark
```

## Available Benchmarks

### Vector Search

- **Small Dataset**: Measures search performance with 100 documents
- **Medium Dataset**: Measures search performance with 1,000 documents
- **Large Dataset**: Measures search performance with 5,000 documents
- **Limit Variations**: Compares search performance with different result limits
- **Hybrid Search**: Measures combined vector-graph search performance
- **RAG Context Retrieval**: Measures performance of context retrieval for RAG
- **Embedding Generation**: Measures performance of generating embeddings for different text lengths

## Benchmark Environment

The benchmarks create a dedicated table in the database with appropriate indexes and test data. This allows measuring performance in isolation without affecting other tests or the application data.

## Interpreting Results

The benchmark results will show:

- **Mean time**: Average execution time
- **Min time**: Minimum execution time
- **Max time**: Maximum execution time
- **StdDev**: Standard deviation of execution times
- **Median time**: Median execution time

Pay special attention to the mean and median times, as they represent the typical performance a user might experience.

## Best Practices

1. **Run in Isolation**: For accurate results, run benchmarks in a clean environment without other processes competing for resources

2. **Run Multiple Times**: Run benchmarks multiple times to ensure consistent results

3. **Test After Changes**: Run benchmarks after making changes to vector search functionality to detect performance regressions

4. **Scale Testing**: Test with different dataset sizes to understand scaling behavior

5. **Profile Bottlenecks**: Use profiling tools to identify bottlenecks in poorly performing areas