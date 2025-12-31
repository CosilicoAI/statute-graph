# Discussion

## Key Findings

Our analysis of Title 26 (Internal Revenue Code) reveals several important structural properties:

### Hub Sections

Section 1 (tax rates) is the most-referenced section, with 563 other sections depending on it. This makes intuitive sense: nearly every tax calculation ultimately depends on the rate schedule. Other major hubs include:

- **Section 401** (qualified pension plans): 238 dependents
- **Section 2** (tax tables): 170 dependents
- **Section 48** (energy credits): 168 dependents

These hub sections should be encoded first to maximize unblocked work.

### Circular References

We identified 1,444 strongly connected components, indicating extensive circular reference patterns. Many of these are trivial (size 1, meaning no actual cycle), but some represent genuine mutual dependencies that require simultaneous consideration.

For example, sections defining income may reference sections defining deductions, which in turn reference income definitions. Such cycles are inherent to the structure of tax law and cannot be eliminated through reordering alone.

### Encoding Implications

The optimal sequence we derive enables:

1. **Parallelization**: Sections at the same "level" in the topological order can be encoded in parallel
2. **Incremental validation**: Each encoded section can be tested against its dependencies
3. **Progress tracking**: The sequence provides a clear metric for encoding completion

## Limitations

1. **Cross-title references**: We focus on Title 26 internal references. Cross-references to other titles (e.g., Title 42 Social Security Act) are noted but not fully resolved.

2. **Temporal dynamics**: Tax law changes frequently. Our snapshot represents the code as of December 2025 {cite:p}`uscode2025`.

3. **Semantic depth**: Not all cross-references are equally important. A definitional reference may be more critical than a cross-reference for administrative purposes.

## Future Work

1. **Multi-title analysis**: Extend to all 54 titles of the US Code
2. **Temporal evolution**: Track how the dependency graph changes over time
3. **Weighted edges**: Assign importance weights to different reference types
4. **Graph neural networks**: Apply techniques from {cite:t}`casegnn2024` for legal case retrieval

## Conclusion

Graph-theoretic analysis of statutory cross-references provides a principled foundation for encoding law into computable form. By identifying hub sections, circular reference groups, and optimal encoding sequences, we enable more systematic approaches to legal technology development.

The `statute-graph` package provides open-source tools for this analysis, available at [github.com/CosilicoAI/statute-graph](https://github.com/CosilicoAI/statute-graph).
