# Optimal Encoding Order for Statutory Cross-References

**A Graph-Theoretic Approach to Compiling Tax Law**

## Abstract

Tax statutes form a complex web of cross-references. Section 32 (Earned Income Tax Credit) references section 151 (dependency exemption), which references section 152 (definition of dependent), creating chains of dependencies that complicate efforts to encode law into executable rules. We model the US Internal Revenue Code as a directed graph where nodes represent statute sections and edges represent cross-references. Using strongly connected component (SCC) decomposition and topological sorting, we derive an optimal encoding sequence that minimizes blocked dependencies. Our analysis of Title 26 reveals 2,448 sections connected by 8,458 cross-references, with Section 1 (tax rates) serving as the primary hub referenced by 563 other sections. We identify 1,444 strongly connected components representing circular reference patterns, and provide an algorithm for resolving these cycles. The resulting encoding sequence enables systematic translation of statutory law into computable rules.

## Key Findings

- **2,448** statute sections in Title 26 (Internal Revenue Code)
- **8,458** cross-references extracted from official XML
- **Section 1** (tax rates) is the most-referenced section (563 dependents)
- **1,444** circular reference groups requiring special handling
- **741** sections can be encoded immediately (no dependencies)

```{tableofcontents}
```
