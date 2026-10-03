# Milestone 1B — Historical identity methodology decision record

Status: **Approved by the product owner.** This record fixes the identity, chassis, visual-attribution, and teammate methodology below. It is a methodology and domain-contract record, not an implementation or a claim of complete historical evidence coverage. The remaining research and presentation decisions are listed at the end.

## Authority and scope

[Milestone 1A](MILESTONE_1A_DECISION_RECORD.md) remains authoritative for championship scoring, eligible results, constructor scoring, sanctions, exclusions, exact calculation, ambiguity, unavailable states, and the preservation of every constructor contributing to a driver's counted championship points. Nothing in this record changes a recorded result or turns a reconstructed result into an official one.

Historical identity, historical usage, and championship contribution answer different questions. A scoring package may change calculated championship contributions; it must not rewrite contemporary constructor attribution or verified historical participation. Final authoritative amended outcomes are the historical default unless a separate “as it stood at the time” analysis is approved later.

## Identity vocabulary

- **Constructor make:** The formal sporting-attribution concept for the constructor of a car in its contemporary championship context. It is distinct from the engine make and from the organisation entering or operating the car.
- **Constructor episode:** A dated historical participation context for a constructor make, independent of individual chassis models. The same make name or source ID can occur in genuinely separate episodes; an episode is not a claim that all similarly named operations were one organisation.
- **Entrant / competitor:** The party under whose entry cars competed, using the terminology applicable to the period. Its identity may differ from the constructor make.
- **Championship entry:** The formally accepted entry and its championship eligibility and standing in the relevant season or event. An entry change can affect championship attribution without itself changing the car's constructor make.
- **Racing operation:** The people, facilities, equipment, and race activity operating an entry. Operational continuity is a historical relationship to establish with evidence, not a synonym for a continuing entry, owner, or constructor.
- **Legal organisation and owner:** The legal entity and its ownership. Neither is automatically identical to a sporting entry or constructor, and either may change while an operation continues.
- **Commercial brand / team name:** The name presented publicly or commercially. Branding alone does not establish constructor-make, entrant, or operational equivalence.
- **Successor operation:** An operation with a supported succession relationship to an earlier one. Succession does not make their constructors, entries, or legal organisations identical.
- **Engine make / manufacturer:** The engine's contemporary make attribution and the entity that manufactured it. Rebadging and supply relationships may make these different; neither determines the chassis constructor make.
- **Works relationship:** A sourced relationship between a manufacturer and an entry or operation. It is separate from constructor, engine, ownership, and customer status.
- **Chassis model / specification:** A technical identity on its own dated timeline, separate from constructor make and episode. An episode can use multiple chassis; a chassis family can span seasons.

Use historically appropriate terminology where formal definitions changed over time. Preserve contemporary attribution and source wording rather than projecting a later definition backward.

## Identity relationships and evidence

Represent and assess **same constructor make**, **separate episode of a make**, **confirmed make change**, **same or changed entrant**, **same or changed championship entry**, **operational succession**, **ownership or legal succession**, **brand change or revival**, **engine change**, and **chassis change** as distinct relationships. A question about any one relationship must not be answered automatically from another.

Ownership, entrant, engine, and chassis changes do **not** by themselves create a new constructor episode. Confirmed constructor-make changes and genuinely separate returns can create episodes. A renamed or reused brand does not establish make continuity; organisational succession does not establish constructor equivalence. Preserve unresolved classifications until evidence supports them.

F1DB's `constructor_id`, `entrant_id`, and `engine_manufacturer_id` are useful but separate source fields. Its chronology records relationships that require interpretation; it is not an automatic identity-equivalence rule. A curated, dated identity layer must retain evidence, provenance, and uncertainty for classifications F1DB cannot establish. In particular, one database constructor ID does not prove one uninterrupted episode, and different IDs do not alone prove the absence of an operational or branding relationship.

## Stable chassis usage — Driver view

Where verified event-level evidence exists, the primary driver-season chassis is the chassis model with the greatest number of **Grand Prix race appearances by that driver** in the target season. Count a driver–model once per GP, even if that driver uses more than one car of the model. More than one model can be recorded at a GP where actual race participation in each is verified. A mere entry, practice, qualifying, or sprint appearance does not establish a GP race appearance.

Retain every other verified chassis and its supported event coverage. If models tie for the greatest number of verified appearances, retain all as **co-primary**. Do not break the tie with wins, points, counted results, or database order. If evidence identifies only a season- or entrant-level chassis set, expose that set but mark primary chassis **unavailable**; do not infer a driver's event usage from the association.

This usage identity is stable across scoring packages.

## Stable chassis usage — Constructor view

Where verified event-level evidence exists, the primary constructor-season chassis is the model with the greatest number of **Grand Prix car starts** across the championship-relevant constructor entries in the target season. Count cars that actually start, not rounds in which a model appears; a shared car contributes one car start. Retain every verified model and supported event coverage. Equal leaders are co-primary without a sporting tie-break. Season- or entrant-level associations alone yield a chassis set, not a primary model.

Fix the usage population to the target season's **verified historical participation under its original championship context**, respecting the applicable Milestone 1A constructor rules for that context. A selected counterfactual package may change championship contribution by chassis, but cannot change this stable primary-chassis usage population. For seasons without an official Constructors' Championship, do not imply that an official constructor championship population existed. Any later analytical constructor participation scope for those seasons requires its own definition and clear label before it can support a constructor-view primary.

## Championship contribution by chassis

For both views, chassis championship contribution is a **scoring-dependent analytical result**, separate from stable usage primary or co-primary status. Attribute event awards and counted results to a model only where event-level evidence and the selected Milestone 1A calculation trace support the attribution. Driver and constructor contribution must follow their respective championship rules, including eligible awards, result limits, historical constructor scoring provisions, sanctions, exclusions, and ambiguity.

An adjustment without a defensible chassis allocation remains explicitly unallocated. If several valid counted-result allocations or event identities produce different chassis contributions, preserve the alternatives or ambiguity. Do not distribute an adjustment proportionally, infer an event chassis from a season association, or force chassis subtotals to explain a total by invention. Distinguish genuine zero from ambiguous and unavailable contribution.

## Multi-constructor Driver chart attribution

Preserve **every constructor contributing to a driver's counted points** and its contribution state in the domain result, as Milestone 1A requires. For a Driver chart season with multiple constructors, the stable chart-colour anchor is the constructor with the greatest **reconstructed Original counted constructor contribution** for that driver-season. This is F1 ERAs' documented visual-attribution convention, **not an official historical primary-constructor designation**.

The official recorded championship result and the reconstructed Original per-constructor contribution breakdown are distinct. Label and provenance must make that distinction clear, including when the reconstruction matches the official season total. Expose the contribution leader under the active counterfactual package separately as an analytical result; changing packages does not recolour the stable historical anchor.

If the reconstructed Original contributions tie, are ambiguous under valid Milestone 1A allocations, or are unavailable, retain **multiple/unresolved** chart attribution. Do not select by database order, appearances, entrant, or another silent fallback. Preserve the full contributing-constructor set even where a unique anchor exists. For a driver who becomes champion only under a counterfactual package, evaluate the same driver's target-season contributions under Original for the colour anchor; do not borrow the recorded champion's identity.

## Teammate eligibility and grouping

Teammates are a **pairwise, dated relationship** between drivers in the same racing operation with verified concurrent GP race participation in at least one common round. Record the overlapping rounds and extent, including partial-season overlap. A shared constructor make alone is insufficient: independent entrants and operations can race the same make. A shared season roster without verified concurrent GP participation is distinct from confirmed concurrent teammates.

Entrant and championship-entry identity are evidence about an operation, not automatic substitutes for it. A documented operation may continue across an entrant replacement while the formal entries and their championship standings remain separate. For a **same-constructor teammate** claim, also verify the same contemporary constructor make during the overlapping participation. In multi-constructor seasons, assess the relationship at the relevant events, not from either driver's season-level chart-colour anchor.

Preserve confirmed concurrent, same-operation-but-not-verified-concurrent, separate-operation, and unresolved states with provenance. Pairwise overlaps are not transitive: overlapping A–B and B–C tenures do not establish A–C concurrent teammate status. A P1–P2 teammate-title-battle fact requires confirmed concurrent participation and must retain overlap extent so a brief overlap cannot be mistaken for an entire-season battle. The eventual visual indication remains separate from driver identity patterns.

## Driver visual identity

Assign restrained driver patterns through a **versioned driver + constructor-episode identity mapping**, independent of championships, wins, points, and the selected scoring package. The former provisional championships → wins → points teammate hierarchy is retired as a pattern-assignment rule. Such performance figures may later appear as contextual statistics, but the pattern means **driver identity only**, never quality, status, dominance, or an upset.

Prefer reuse of a driver's motif across constructor episodes where practical, without making global reuse an invariant. Where motifs conflict, clarity among drivers in the relevant constructor episode and display context takes precedence. Preserve published assignments when adding drivers where practical; exact pattern vocabulary, collision policy, and rendering remain presentation decisions. The P1–P2 teammate-title-battle indicator has a separate meaning and must not be encoded as a driver pattern.

## Shared domain and future information contract

Driver and Constructor views must derive from one coherent historical domain layer, exposing applicable constructor make and episode, entrant or entry, operation, chassis model/specification, engine make and manufacturer, works/customer relationship where supported, all verified chassis, primary/co-primary status, scoring-dependent chassis contribution, provenance, ambiguity, and unavailable states. Their championship calculations and eligibility need not be identical.

The domain should support concise hover facts and fuller detail: identity, verified chassis and event coverage, engines where relevant, contributing constructors or entries, championship gap/context, active scoring package, teammate-title-battle status in Driver view, chassis contributions, and evidence status. This is an information contract, not a tooltip or detail-layout design.

Keep official recorded Original standings distinct from reconstructed matching standings and counterfactual rescoring. Exact calculation values must govern scoring, ranking, result limits, and countback; display rounding cannot affect them. A counterfactual explanation should eventually show both how the result was calculated and why it differs from Original using the Milestone 1A trace where possible. Future reproducible/shareable state should include scoring package, season range, Driver/Constructor mode, metric, and relevant visual settings.

## Historical cases and source limits

The curated identity layer should be checked against, at minimum, the Jordan → Midland → Spyker → Force India → Racing Point → Aston Martin succession, Tyrrell → BAR → Honda → Brawn → Mercedes, Sauber → BMW Sauber → Sauber → Alfa Romeo → Sauber/Audi, distinct Lotus usages, the separate Mercedes 1954–55 and modern participation contexts, historical Alfa Romeo works activity versus its later Sauber branding, and the 2018 Force India entrant transition. Listing a chain here identifies a research case; it **does not** declare its members the same constructor. The [FIA's 2018 decision](https://www.fia.com/news/fia-approves-mid-season-entry-racing-point-force-india) documents why entrant transition, operational continuity, and Constructors' Championship treatment must be kept separate. [Formula 1's account of Rob Walker's Cooper](https://www.formula1.com/en/latest/article/argentina-58-moss-bluffs-his-way-to-victory-and-ushers-in-new-era.g34lnPj7q41eIAS0HbA9d) illustrates why a constructor make need not identify one racing operation.

The inspected F1DB `season_entrant_chassis` records season/entrant associations, while `race_data` has no chassis or entrant field. Those associations cannot alone establish a driver's GP chassis appearances, a constructor's chassis car starts, or chassis-level championship contribution. Event-level evidence and curated operation relationships require source-linked research. Unsupported historical claims remain partial, ambiguous, or unavailable.

## First proof of concept and deferred decisions

The first PoC may deliberately use a **curated subset of historical seasons and cases with sufficient verified evidence**. It must not imply equal evidence coverage across all seasons. Unsupported seasons or fields use explicit partial, ambiguous, or unavailable states rather than inferred values. The PoC should demonstrate that the shared domain represents those states correctly so broader historical coverage can be added without redesigning its identity model.

Before the PoC asserts a particular chassis primary or contribution, establish event-level evidence and rules for GP race appearance, car start, shared-car cases, and model/specification attribution in its curated cases. Where that evidence is absent, show only supported associations and an unavailable primary or contribution. Before rendering a unique multi-constructor colour, verify the reconstructed Original counted-contribution comparison; otherwise use multiple/unresolved attribution. If patterns are rendered, use a fixed, versioned mapping for the displayed drivers. Confirmed teammate-title-battle claims require sourced operation and round overlap.

Intentionally deferred beyond the first PoC are comprehensive historical event-level chassis coverage; full historical colour curation; exact modern-colour eligibility mappings; exact era-preset boundaries; full engine lineage and rebadging research; exhaustive racing-operation succession curation; final tooltip and detail layouts; complete pattern vocabulary and rendering; and visual-regression implementation. These items remain open Milestone 1B or downstream work as appropriate. Their absence does not authorise invented historical identities or calculations.
