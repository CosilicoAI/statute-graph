# Optimal Encoding Sequence for Statutory Cross-References

**Cosilico**

team@cosilico.ai

## Abstract

Tax statutes form a complex web of cross-references. Section 32 (Earned Income Tax Credit) references section 151 (dependency exemption), which references section 152 (definition of dependent), creating chains of dependencies that complicate efforts to encode law into executable rules. We model the US Internal Revenue Code as a directed graph where nodes represent statute sections and edges represent cross-references. Using strongly connected component (SCC) decomposition and topological sorting, we derive an optimal encoding sequence that minimizes blocked dependencies. Our analysis of Title 26 reveals 2,448 sections connected by 8,458 cross-references, with Section 1 (tax rates) serving as the primary hub referenced by 563 other sections. We identify 1,444 strongly connected components, with 40 multi-node components representing circular reference patterns, and provide an algorithm for resolving these cycles. The resulting encoding sequence enables systematic translation of statutory law into computable rules.

**Keywords:** legal informatics, graph theory, statutory analysis, computable law, topological sort

## Introduction

### The Problem of Statutory Complexity

Tax law is not a collection of independent rules. Each section of the Internal Revenue Code references other sections, creating a web of dependencies that must be understood before any section can be correctly interpreted or encoded into executable form.

Consider the Earned Income Tax Credit (EITC), codified at 26 USC § 32. This single section references Section 1 (tax rates), Section 151 (dependency exemption), Section 152 (definition of dependent), Section 911 (foreign earned income exclusion), Section 7703 (marital status), and many more. To correctly encode Section 32, one must first understand all of these referenced sections. But those sections themselves have dependencies, creating chains that can extend deeply into the code.

```{figure} _static/figures/network_sample.png
:name: fig-network
:width: 80%

**Figure 1: Cross-Reference Network Around §32 (EITC).** Arrows point from dependent sections to their dependencies. Section 32 depends on foundational sections (§1, §2) and intermediate definitions (§152, §151). The optimal encoding order reverses this direction: encode foundations first, then dependents.
```

### The Encoding Challenge

When translating statute into executable rules (for microsimulation, tax preparation software, or policy analysis), the order of encoding matters:

1. **Forward references** cause problems: If Section A references Section B, encoding A before B requires placeholder logic that must be updated later.

2. **Circular references** require simultaneous encoding: Some sections mutually reference each other, making strict ordering impossible.

3. **Hub sections** block many others: Sections like § 1 (tax rates) are referenced by hundreds of other sections. Encoding these first unblocks the most work.

### Contribution

We present a graph-theoretic framework for analyzing statutory cross-references and deriving optimal encoding sequences. Our approach:

1. Parses official US Code XML to extract structured cross-references
2. Models the statute as a directed graph
3. Identifies circular reference groups using strongly connected component (SCC) analysis {cite:p}`tarjan1972`
4. Produces a topological ordering that respects dependencies while handling cycles

This is, to our knowledge, the first application of dependency graph analysis to statutory encoding order. Prior work on legal citation networks {cite:p}`fowler2007network,katz2020complex` has focused on case law (judicial opinions citing prior decisions) rather than statutory cross-references.

## Methods

### Data Source

We use the official US Code XML from the Office of the Law Revision Counsel (OLRC) {cite:p}`uscode2025`, available at [uscode.house.gov](https://uscode.house.gov/download/download.shtml). The XML uses the United States Legislative Markup (USLM) schema and includes structured cross-reference tags:

```xml
<ref href="/us/usc/t26/s151">section 151 of this title</ref>
```

These tags provide precise citation paths, avoiding the ambiguity of regex-based extraction from plain text.

### Graph Construction

We model the statute as a directed graph $G = (V, E)$ where:

- **Nodes** $V$: Statute sections (e.g., `26 USC § 32`)
- **Edges** $E$: Cross-references, where edge $(u, v)$ means section $u$ references section $v$

Edge direction follows **dependency semantics**: if $A \to B$, then $A$ depends on $B$ and $B$ should be encoded before $A$.

### Strongly Connected Components

A **strongly connected component** (SCC) is a maximal set of nodes where every node is reachable from every other node. In statutory terms, an SCC represents a group of sections that mutually reference each other, either directly or through intermediaries.

For such groups, there is no valid linear ordering where all dependencies come first. We handle this by:

1. **Condensing** each SCC into a single "super-node"
2. **Topologically sorting** the resulting DAG
3. **Expanding** each super-node, ordering internal nodes by importance (out-degree)

This approach follows Tarjan's algorithm {cite:p}`tarjan1972` for SCC detection with $O(V + E)$ complexity.

### Optimal Encoding Algorithm

The complete algorithm proceeds as follows:

1. Compute all SCCs using Tarjan's algorithm
2. Build condensation graph where each SCC is a node
3. Topologically sort the condensation (guaranteed to be a DAG)
4. For each SCC in topological order:
   - If single node: add directly to sequence
   - If multi-node: sort by out-degree (most-referenced first) and add

This produces a sequence where all acyclic dependencies are satisfied (dependency comes before dependent), and within cycles, hub nodes (most referenced) come first.

```{figure} _static/figures/dependency_flow.png
:name: fig-flow
:width: 90%

**Figure 2: Optimal Encoding Order by Dependency Level.** Foundation sections (§1 Tax Rates, §2 Tax Tables, §7701 Definitions) should be encoded first, followed by core concepts, deductions, and finally credits like the EITC.
```

## Results

### Graph Statistics

Our analysis of Title 26 (Internal Revenue Code) yields:

| Metric | Value |
|--------|-------|
| Sections (nodes) | 2,448 |
| Cross-references (edges) | 8,458 |
| Graph density | 0.0014 |
| Average dependencies per section | 3.5 |
| Strongly connected components | 1,444 |

The low density (0.14%) indicates that despite extensive cross-referencing, most section pairs are not directly connected. The average section depends on approximately 3-4 other sections.

### Hub Sections

The most-referenced sections serve as "hubs" in the dependency graph. These should be encoded first to unblock the most dependent sections.

```{figure} _static/figures/hub_sections.png
:name: fig-hubs
:width: 85%

**Figure 3: Most-Referenced Sections in Title 26.** Section 1 (tax rates) dominates with 563 dependent sections—nearly a quarter of all sections reference it. Other hubs include §401 (qualified pension plans), §2 (tax tables), and §48 (energy credits).
```

Section 1 (tax rates) is the most-referenced section, with 563 other sections depending on it. This makes intuitive sense: nearly every tax calculation ultimately depends on the rate schedule. Other major hubs include:

- **Section 401** (qualified pension plans): 238 dependents
- **Section 2** (tax tables): 170 dependents
- **Section 48** (energy credits): 168 dependents
- **Section 23** (adoption credit): 130 dependents

### Circular Reference Patterns

```{figure} _static/figures/scc_distribution.png
:name: fig-scc
:width: 90%

**Figure 4: Distribution of Strongly Connected Components.** Left: Most SCCs contain a single section (no cycles). Right: 97% of sections have no circular references; 3% are involved in mutual reference patterns requiring special handling.
```

We identified 1,444 strongly connected components. The majority (1,400+) are trivial single-node SCCs, indicating no circular dependencies. However, 40 multi-node SCCs represent genuine mutual dependencies.

For example, sections defining income may reference sections defining deductions, which in turn reference income definitions. Such cycles are inherent to the structure of tax law and cannot be eliminated through reordering alone.

### Degree Distribution

```{figure} _static/figures/degree_distribution.png
:name: fig-degrees
:width: 90%

**Figure 5: Dependency Distributions.** Left: Number of dependencies (in-degree) per section—most sections depend on 0-10 others. Right: Number of dependents (out-degree) per section—follows a power-law distribution with a long tail of highly-referenced hub sections.
```

The in-degree distribution (dependencies) is roughly exponential: most sections depend on few others, with a mean of 3.5. The out-degree distribution (dependents) shows a power-law tail characteristic of scale-free networks, with a few hub sections referenced by hundreds of others.

### Encoding Sequence

The optimal encoding sequence enables:

1. **Parallelization**: Sections at the same "level" in the topological order can be encoded in parallel
2. **Incremental validation**: Each encoded section can be tested against its dependencies
3. **Progress tracking**: The sequence provides a clear metric for encoding completion

The first 10 sections to encode are foundational definitions and rate tables. The last sections to encode are highly specific provisions that depend on many others.

## Discussion

### Implications for Legal Technology

This analysis has practical implications for projects encoding law into computable form:

1. **Project planning**: The encoding sequence provides a principled order for tackling sections, minimizing rework from forward references.

2. **Resource allocation**: Hub sections require more careful encoding since errors propagate to many dependents.

3. **Testing strategy**: Sections can be tested incrementally as their dependencies are completed.

### Limitations

1. **Cross-title references**: We focus on Title 26 internal references. Cross-references to other titles (e.g., Title 42 Social Security Act) are noted but not fully resolved.

2. **Temporal dynamics**: Tax law changes frequently. Our snapshot represents the code as of December 2025 {cite:p}`uscode2025`.

3. **Semantic depth**: Not all cross-references are equally important. A definitional reference may be more critical than a cross-reference for administrative purposes.

### Future Work

1. **Multi-title analysis**: Extend to all 54 titles of the US Code
2. **Temporal evolution**: Track how the dependency graph changes over time
3. **Weighted edges**: Assign importance weights to different reference types
4. **Graph neural networks**: Apply techniques from {cite:t}`casegnn2024` for legal case retrieval

## Conclusion

Graph-theoretic analysis of statutory cross-references provides a principled foundation for encoding law into computable form. By identifying hub sections, circular reference groups, and optimal encoding sequences, we enable more systematic approaches to legal technology development.

The `statute-graph` package provides open-source tools for this analysis, available at [github.com/CosilicoAI/statute-graph](https://github.com/CosilicoAI/statute-graph).

## References

```{bibliography}
```
