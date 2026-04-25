# engine/reporter.py
# Dynamic report generator — fully domain-agnostic
# All text is generated from actual JD/candidate data

from engine.ranker import compare_top_two


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def fmt_list(items: list, max_items: int = 6) -> str:
    """Format a list into a readable comma-separated string."""
    if not items:
        return "N/A"
    shown = items[:max_items]
    text = ", ".join(shown)
    if len(items) > max_items:
        text += f" (+{len(items) - max_items} more)"
    return text


def pct_bar(score: float, max_score: float) -> str:
    """Simple text-based progress bar."""
    ratio = score / max_score if max_score > 0 else 0
    filled = int(ratio * 10)
    return "█" * filled + "░" * (10 - filled)


# ─────────────────────────────────────────────
# Simulated Conversation (Dynamic)
# ─────────────────────────────────────────────

def generate_conversation(candidate: dict, jd: dict) -> str:
    """Generate a realistic simulated recruiter-candidate conversation."""
    name = candidate.get("name", "Candidate")
    role = jd.get("role", "this role")
    domain = jd.get("domain", "this field")
    match = candidate.get("match_score", 0)
    exp = candidate.get("experience", 0)
    ownership = candidate.get("ownership", "basic")

    # Get top matched skills for the conversation
    gap = candidate.get("skill_gap", {})
    matched_skills = [m["jd_skill"] for m in gap.get("matched", [])][:3]
    missing_skills = [g["jd_skill"] for g in gap.get("gaps", [])][:2]

    skill_mention = fmt_list(matched_skills, 3) if matched_skills else domain

    lines = []
    lines.append("**Recruiter:**")
    lines.append(f"Hi {name}, we have an opening for a **{role}** that seems to align with your background. Would you be interested in learning more?\n")

    lines.append(f"**{name}:**")

    # Dynamic response based on BOTH match AND seniority
    if exp >= 7:
        # Senior — selective, confident tone
        if match >= 80:
            lines.append(
                f"I've spent significant time building depth in {skill_mention}. "
                f"This role looks well-aligned — I'd be interested in understanding the team structure "
                f"and the kind of challenges you're solving at this level.\n"
            )
        elif match >= 60:
            lines.append(
                f"There's meaningful overlap with my work in {skill_mention}. "
                f"At my level, I'm quite selective about transitions — I'd want to understand "
                f"the scope, leadership expectations, and what differentiates this opportunity.\n"
            )
        else:
            lines.append(
                f"I appreciate the outreach. However, my expertise is fairly specialized at this point, "
                f"and this role in {domain} doesn't seem like the right alignment for where I'm headed.\n"
            )
    elif exp >= 4:
        # Mid-level — balanced, growth-oriented tone
        if match >= 80:
            lines.append(
                f"That sounds like a great fit. My experience in {skill_mention} "
                f"aligns well with what you're describing. I'd be happy to discuss further "
                f"and learn about the growth path in this role.\n"
            )
        elif match >= 60:
            lines.append(
                f"This looks interesting. I have experience with {skill_mention}, "
                f"which seems relevant. I'd like to learn more about the scope, "
                f"team dynamics, and how this could accelerate my career.\n"
            )
        else:
            lines.append(
                f"Some aspects like {skill_mention} overlap with my background, "
                f"but I'd need to understand the full scope before considering a move.\n"
            )
    else:
        # Junior — eager, learning-focused tone
        if match >= 60:
            lines.append(
                f"This sounds exciting! I've been working with {skill_mention} "
                f"and I'm eager to grow in this area. I'd love to hear more about "
                f"the mentorship and learning opportunities in this role.\n"
            )
        elif match >= 40:
            lines.append(
                f"I'm early in my career and actively looking to build depth. "
                f"I have some exposure to {skill_mention} and this role could be "
                f"a great learning opportunity. I'd definitely like to know more.\n"
            )
        else:
            lines.append(
                f"Thanks for reaching out. I'm still exploring what direction to take "
                f"in my career, and I'm not sure this particular role in {domain} "
                f"is the right fit for me right now.\n"
            )

    # Follow-up Q&A — also dynamic by seniority
    lines.append("**Follow-up Q&A:**\n")

    # Open to switch?
    if exp >= 7:
        if match >= 75:
            switch = "For the right role, yes. I'm looking for impact and ownership, not just a title change."
        elif match >= 55:
            switch = "I'd need a compelling reason — my current work is challenging and well-compensated."
        else:
            switch = "Not actively looking. I'd only consider something significantly differentiated."
    elif exp >= 4:
        if match >= 70:
            switch = "Yes, I'm open to roles that offer the right mix of challenge and growth."
        elif match >= 50:
            switch = "Open to exploring if the role and culture are a good fit."
        else:
            switch = "Possibly, but I'd want to see a clear alignment with my skills first."
    else:
        if match >= 50:
            switch = "Absolutely — I'm actively looking for opportunities to learn and grow."
        else:
            switch = "I'm open to opportunities, but I want to make sure I can contribute meaningfully."

    lines.append(f"- **Q:** Are you open to exploring new opportunities?")
    lines.append(f"  **A:** {switch}\n")

    # Work preference — varies by seniority
    if exp >= 7:
        work_pref = "Flexible — but I value focused, deep-work time. Remote or hybrid works best for me."
    elif exp >= 4:
        work_pref = "Hybrid is ideal — I value both collaboration and independent work time."
    else:
        work_pref = "I'm open to any setup. Being close to the team would help me ramp up faster."

    lines.append(f"- **Q:** Preferred work arrangement?")
    lines.append(f"  **A:** {work_pref}\n")

    # What excites you?
    if exp >= 7 and ownership == "end-to-end":
        excite = (f"Driving complex outcomes end-to-end. If this role involves "
                  f"real ownership and hard technical problems in {domain}, I'm interested.")
    elif exp >= 4 and match >= 60:
        excite = (f"Deepening my expertise in {skill_mention} while taking on "
                  f"more responsibility. I want to grow toward end-to-end ownership.")
    elif exp < 4:
        excite = (f"The chance to learn from experienced engineers and build a "
                  f"strong foundation in {domain}. I'm motivated by steep learning curves.")
    else:
        excite = "I'd need to understand the day-to-day and team culture better before answering that."

    lines.append(f"- **Q:** What would excite you about this role?")
    lines.append(f"  **A:** {excite}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Match Explanation (Dynamic)
# ─────────────────────────────────────────────

def generate_explanation(candidate: dict, jd: dict) -> str:
    """Generate dynamic match/interest explanation."""
    lines = []
    name = candidate.get("name", "Candidate")
    match = candidate.get("match_score", 0)
    interest = candidate.get("interest_score", 0)
    breakdown = candidate.get("match_breakdown", {})
    gap = candidate.get("skill_gap", {})
    ownership = candidate.get("ownership", "basic")
    exp = candidate.get("experience", 0)
    jd_role = jd.get("role", "the role")

    matched = gap.get("matched", [])
    gaps = gap.get("gaps", [])

    # ── Match Reasoning ──
    lines.append("**Match Reasoning:**\n")

    # Skills analysis
    if breakdown.get("required_skills", 0) >= 35:
        top_matches = [m["jd_skill"] for m in matched[:4]]
        lines.append(f"- Strong skill alignment with {fmt_list(top_matches)}")
    elif breakdown.get("required_skills", 0) >= 25:
        lines.append(f"- Decent skill overlap ({len(matched)}/{len(matched) + len(gaps)} required skills matched)")
    else:
        lines.append(f"- Limited skill match ({len(matched)}/{len(matched) + len(gaps)} required skills)")

    # Gaps
    if gaps:
        gap_names = [g["jd_skill"] for g in gaps[:3]]
        lines.append(f"- Gaps identified: {fmt_list(gap_names)}")

    # Tools
    tool_score = breakdown.get("tools", 0)
    if tool_score >= 18:
        lines.append("- Excellent tool proficiency match")
    elif tool_score >= 12:
        lines.append("- Partial tool match — some key tools covered")
    else:
        lines.append("- Limited tool overlap with requirements")

    # Experience
    exp_score = breakdown.get("experience", 0)
    min_exp = jd.get("experience_min", 0)
    max_exp = jd.get("experience_max", 100)

    if min_exp <= exp <= max_exp:
        lines.append(f"- Experience ({exp} yrs) fits the {min_exp}–{max_exp} yr range well")
    elif exp > max_exp:
        overshoot = round(exp - max_exp, 1)
        if overshoot <= 1:
            lines.append(f"- Slightly above range ({exp} yrs vs {min_exp}–{max_exp}) — minimal concern")
        else:
            lines.append(f"- Over-experienced ({exp} yrs vs {min_exp}–{max_exp} yr range) — may be overqualified")
    else:
        shortfall = round(min_exp - exp, 1)
        if shortfall <= 0.5:
            lines.append(f"- Slightly below required range ({exp} yrs vs {min_exp}–{max_exp}) but acceptable")
        elif shortfall <= 1.5:
            lines.append(f"- Under-experienced ({exp} yrs vs {min_exp}–{max_exp} yr requirement) — may need ramp-up")
        else:
            lines.append(f"- Significantly under-experienced ({exp} yrs vs {min_exp}–{max_exp} yr requirement)")

    # Ownership
    own_score = breakdown.get("ownership", 0)
    if own_score >= 9:
        lines.append(f"- {ownership.title()} ownership level — strong independent contributor")
    elif own_score >= 7:
        lines.append(f"- {ownership.title()}-level ownership — solid contributor")
    else:
        lines.append(f"- {ownership.title()}-level ownership — may need mentorship/ramp-up")

    # ── Interest Reasoning ──
    lines.append("\n**Interest Reasoning:**\n")

    i_breakdown = candidate.get("interest_breakdown", {})

    if interest >= 80:
        lines.append(f"- High predicted interest — role aligns well with {name}'s profile and career stage")
    elif interest >= 65:
        lines.append(f"- Moderate interest — {name} is likely open to exploring this opportunity")
    elif interest >= 50:
        lines.append(f"- Cautious interest — {name} may need convincing on the role's value proposition")
    else:
        lines.append(f"- Low predicted interest — significant misalignment with {name}'s goals")

    role_align = i_breakdown.get("role_alignment", 0)
    if role_align >= 35:
        lines.append("- Strong role-profile alignment")
    elif role_align >= 25:
        lines.append("- Partial role-profile alignment")

    growth = i_breakdown.get("growth_potential", 0)
    if growth >= 16:
        lines.append("- Good growth opportunity for this candidate")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Full Report Generator
# ─────────────────────────────────────────────

def generate_report(jd: dict, candidates: list) -> str:
    """
    Generate complete hiring analysis report.
    Fully dynamic — no hardcoded domain text.
    """
    report = []

    role = jd.get("role", "Not Specified")
    domain = jd.get("domain", "General")
    min_exp = jd.get("experience_min", 0)
    max_exp = jd.get("experience_max", 0)

    # ─── Header ───
    report.append("# 🤖 TalentScout AI — Hiring Analysis Report\n")
    report.append(f"**Domain Detected:** {domain}")
    report.append(f"**Role:** {role}")
    if min_exp and max_exp and max_exp < 100:
        report.append(f"**Experience Range:** {min_exp}–{max_exp} years")
    report.append(f"**Candidates Evaluated:** {len(candidates)}\n")

    # ─── Scoring Methodology ───
    report.append("---\n")
    report.append("## ⚖️ Scoring Methodology\n")
    report.append("**Match Score** (Technical Fit / 100): Required Skills (40) + Tools (20) + Experience (20) + Preferred Skills (10) + Ownership (10)\n")
    report.append("**Interest Score** (Behavioral Fit / 100): Role Alignment (40) + Seniority Fit (20) + Growth (20) + Selectiveness (20)\n")
    report.append("**Final Score** = (0.7 × Match) + (0.3 × Interest)\n")

    # ─── Candidate Evaluations ───
    report.append("---\n")
    report.append("## 📊 Candidate Evaluations\n")

    for c in candidates:
        rank = c.get("rank", "?")
        name = c.get("name", "Unknown")
        verdict = c.get("verdict", "N/A")
        tier = c.get("tier", "")
        confidence = c.get("confidence", 0)

        report.append(f"---\n")
        report.append(f"### #{rank} — {name}\n")
        report.append(f"**Verdict: {verdict}** | Tier: {tier} | Confidence: {confidence}%\n")

        # Score summary
        ms = c.get("match_score", 0)
        isc = c.get("interest_score", 0)
        fs = c.get("final_score", 0)
        bd = c.get("match_breakdown", {})

        report.append(f"| Metric | Score |")
        report.append(f"|--------|-------|")
        report.append(f"| **Match Score** | **{ms}**/100 |")
        report.append(f"| ↳ Required Skills | {bd.get('required_skills', 0)}/40 |")
        report.append(f"| ↳ Tools | {bd.get('tools', 0)}/20 |")
        report.append(f"| ↳ Experience | {bd.get('experience', 0)}/20 |")
        report.append(f"| ↳ Preferred Skills | {bd.get('preferred_skills', 0)}/10 |")
        report.append(f"| ↳ Ownership | {bd.get('ownership', 0)}/10 |")
        report.append(f"| **Interest Score** | **{isc}**/100 |")
        report.append(f"| **Final Score** | **{fs}**/100 |")
        report.append("")

        # Skill gap visualization
        gap = c.get("skill_gap", {})
        matched = gap.get("matched", [])
        gaps = gap.get("gaps", [])

        if matched or gaps:
            report.append("**Skill Analysis:**\n")
            for m in matched:
                report.append(f"- ✅ {m['jd_skill']} ← _{m['candidate_skill']}_ ({m['score']:.2f})")
            for g in gaps:
                report.append(f"- ❌ {g['jd_skill']} — closest: _{g['closest']}_ ({g['score']:.2f})")
            report.append("")

        # Simulated conversation
        report.append("#### 💬 Simulated Conversation\n")
        report.append(generate_conversation(c, jd))
        report.append("")

        # Explanation
        report.append("#### 🧠 Explanation\n")
        report.append(generate_explanation(c, jd))
        report.append("")

    # ─── Final Ranking ───
    report.append("---\n")
    report.append("## 🏆 Final Ranking\n")
    report.append("| Rank | Candidate | Final Score | Verdict |")
    report.append("|------|-----------|-------------|---------|")
    for c in candidates:
        report.append(
            f"| #{c.get('rank', '?')} | **{c['name']}** | "
            f"{c.get('final_score', 0)} | {c.get('verdict', 'N/A')} |"
        )
    report.append("")

    # ─── Head-to-Head Comparison ───
    if len(candidates) >= 2:
        report.append("---\n")
        report.append("## 🔍 Head-to-Head: #1 vs #2\n")

        comp = compare_top_two(candidates)
        c1 = comp.get("candidate_1", "")
        c2 = comp.get("candidate_2", "")
        diff = comp.get("score_diff", 0)

        report.append(f"**{c1}** leads **{c2}** by **{diff} points**.\n")

        adv1 = comp.get("advantages_1", [])
        adv2 = comp.get("advantages_2", [])

        if adv1:
            report.append(f"**{c1} advantages:**")
            for a in adv1:
                report.append(f"- {a}")
            report.append("")

        if adv2:
            report.append(f"**{c2} advantages:**")
            for a in adv2:
                report.append(f"- {a}")
            report.append("")

        if comp.get("experience_note"):
            report.append(f"📌 {comp['experience_note']}")
        if comp.get("ownership_note"):
            report.append(f"📌 {comp['ownership_note']}")
        report.append("")

    # ─── Final Insight ───
    report.append("---\n")
    report.append("## 🧠 Final Hiring Decision\n")

    strong_hires = [c for c in candidates if c.get("verdict") == "Strong Hire"]
    hires = [c for c in candidates if c.get("verdict") == "Hire"]
    considers = [c for c in candidates if c.get("verdict") == "Consider"]

    if strong_hires:
        names = ", ".join([c["name"] for c in strong_hires])
        report.append(f"**Strong Hire recommendation:** {names}")
        report.append(f"These candidates show excellent alignment with the {role} role and are highly recommended for interviews.\n")

    if hires:
        names = ", ".join([c["name"] for c in hires])
        report.append(f"**Hire recommendation:** {names}")
        report.append(f"Solid candidates worth interviewing for the {role} position.\n")

    if considers:
        names = ", ".join([c["name"] for c in considers])
        report.append(f"**Consider:** {names}")
        report.append(f"These candidates have potential but may need further evaluation or upskilling.\n")

    no_rec = [c for c in candidates if c.get("verdict") in ("Not Recommended", "Needs Evaluation")]
    if no_rec:
        names = ", ".join([c["name"] for c in no_rec])
        report.append(f"**Not recommended at this time:** {names}\n")

    if not strong_hires and not hires:
        report.append("⚠️ **No strong candidates found. Consider sourcing additional profiles or adjusting requirements.**")

    # ─── Recruiter Actions ───
    report.append("\n---\n")
    report.append("## 📌 Recommended Actions\n")

    for c in candidates:
        name = c.get("name", "Unknown")
        verdict = c.get("verdict", "N/A")
        match = c.get("match_score", 0)
        ownership = c.get("ownership", "basic")
        exp = c.get("experience", 0)
        gap = c.get("skill_gap", {})
        matched = gap.get("matched", [])
        gaps = gap.get("gaps", [])

        # Build strength description from top matched skills
        top_strengths = [m["jd_skill"] for m in matched[:3]]
        strength_text = fmt_list(top_strengths, 3) if top_strengths else "general skills"

        if verdict == "Strong Hire":
            if ownership == "end-to-end" and exp >= 6:
                report.append(f"- **Interview {name}** for senior/lead roles requiring {strength_text} and end-to-end ownership")
            else:
                report.append(f"- **Interview {name}** — strong alignment in {strength_text}")
        elif verdict == "Hire":
            if gaps:
                gap_text = fmt_list([g["jd_skill"] for g in gaps[:2]], 2)
                report.append(f"- **Interview {name}** — solid fit; probe depth in {gap_text} during interview")
            else:
                report.append(f"- **Interview {name}** — good overall fit for the role")
        elif verdict == "Consider":
            if gaps:
                gap_text = fmt_list([g["jd_skill"] for g in gaps[:2]], 2)
                report.append(f"- **Consider {name}** for pipeline/backup — upskill needed in {gap_text}")
            else:
                report.append(f"- **Consider {name}** for junior or growth-track positions")
        elif verdict == "Needs Evaluation":
            report.append(f"- **Hold {name}** — significant gaps; consider for junior/trainee pipeline if team has mentorship capacity")
        else:
            report.append(f"- **Pass on {name}** — insufficient alignment with current requirements")

    report.append("")

    # ─── Agent Reasoning Steps ───
    report.append("---\n")
    report.append("## 🧠 Agent Reasoning Steps\n")

    jd_skills_count = len(jd.get("required_skills", []))
    pref_count = len(jd.get("preferred_skills", []))
    tool_count = len(jd.get("tools", []))

    report.append(f"1. **Parsed JD** → extracted {jd_skills_count} required skills, "
                  f"{pref_count} preferred skills, {tool_count} tools")
    report.append(f"2. **Detected Domain** → {jd.get('domain', 'General')}")
    report.append(f"3. **Parsed {len(candidates)} candidates** → extracted skills, tools, experience, ownership level")
    report.append(f"4. **Semantic matching** → used hybrid similarity (token + embedding) with compound skill support")
    report.append(f"5. **Scored candidates** → weighted model: Skills (40) + Tools (20) + Experience (20) + Preferred (10) + Ownership (10)")
    report.append(f"6. **Simulated interest** → behavioral scoring based on role alignment, seniority, growth potential")
    report.append(f"7. **Ranked & decided** → Final = (0.7 × Match) + (0.3 × Interest) → verdicts assigned")

    # Check if any inferred skills were used
    inferred_used = any(c.get("inferred_skills") for c in candidates)
    if inferred_used:
        report.append(f"8. **Implicit skill inference** → inferred additional skills from candidate context (e.g., 'end-to-end PD' implies PnR, Placement, CTS, Routing)")

    return "\n".join(report)