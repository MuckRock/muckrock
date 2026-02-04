"""
Utilities for exporting jurisdiction data to Markdown format
"""

# Django
from django.db.models import Count, Q

# Third Party
from bs4 import BeautifulSoup

# MuckRock
from muckrock.agency.models import Agency
from muckrock.core.stats import collect_stats
from muckrock.jurisdiction.models import Jurisdiction


def _html_to_markdown(html_content):  # pylint: disable=too-many-branches
    """Convert HTML content to Markdown format

    Args:
        html_content: String containing HTML

    Returns:
        String with Markdown formatting
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")

    # Convert specific HTML elements to Markdown
    for tag in soup.find_all("h1"):
        tag.string = f"\n# {tag.get_text()}\n"
        tag.unwrap()

    for tag in soup.find_all("h2"):
        tag.string = f"\n## {tag.get_text()}\n"
        tag.unwrap()

    for tag in soup.find_all("h3"):
        tag.string = f"\n### {tag.get_text()}\n"
        tag.unwrap()

    for tag in soup.find_all("h4"):
        tag.string = f"\n#### {tag.get_text()}\n"
        tag.unwrap()

    for tag in soup.find_all("h5"):
        tag.string = f"\n##### {tag.get_text()}\n"
        tag.unwrap()

    for tag in soup.find_all("h6"):
        tag.string = f"\n###### {tag.get_text()}\n"
        tag.unwrap()

    # Convert blockquotes
    for tag in soup.find_all("blockquote"):
        lines = tag.get_text().strip().split("\n")
        quoted = "\n".join(f"> {line}" for line in lines)
        tag.string = f"\n{quoted}\n"
        tag.unwrap()

    # Convert unordered lists
    # pylint: disable=invalid-name
    for ul in soup.find_all("ul"):
        list_items = []
        for li in ul.find_all("li", recursive=False):
            list_items.append(f"- {li.get_text().strip()}")
        ul.string = "\n" + "\n".join(list_items) + "\n"
        ul.unwrap()

    # Convert ordered lists
    for ol in soup.find_all("ol"):
        list_items = []
        for i, li in enumerate(ol.find_all("li", recursive=False), 1):
            list_items.append(f"{i}. {li.get_text().strip()}")
        ol.string = "\n" + "\n".join(list_items) + "\n"
        ol.unwrap()
    # pylint: enable=invalid-name

    # Convert strong/bold
    for tag in soup.find_all(["strong", "b"]):
        tag.string = f"**{tag.get_text()}**"
        tag.unwrap()

    # Convert emphasis/italic
    for tag in soup.find_all(["em", "i"]):
        tag.string = f"*{tag.get_text()}*"
        tag.unwrap()

    # Convert links
    for tag in soup.find_all("a"):
        href = tag.get("href", "")
        text = tag.get_text()
        if href:
            tag.string = f"[{text}]({href})"
        else:
            tag.string = text
        tag.unwrap()

    # Get the text content
    text = soup.get_text()

    # Clean up extra whitespace and normalize line breaks
    lines = [line.rstrip() for line in text.split("\n")]

    # Remove excessive blank lines (more than 2 in a row)
    cleaned_lines = []
    blank_count = 0
    for line in lines:
        if not line.strip():
            blank_count += 1
            if blank_count <= 2:
                cleaned_lines.append(line)
        else:
            blank_count = 0
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()


def jurisdiction_to_markdown(
    jurisdiction, include_stats=True, include_requests=True, base_url=""
):
    """Generate Markdown representation of jurisdiction page

    Args:
        jurisdiction: Jurisdiction model instance
        include_stats: Boolean (default True) - include statistics section
        include_requests: Boolean (default True) - include recent requests section
        base_url: Optional base URL for generating absolute links

    Returns:
        str: Complete Markdown document
    """
    sections = []

    # Header Section
    sections.append(_generate_header(jurisdiction, base_url))

    # Overview Section
    overview = _generate_overview(jurisdiction)
    if overview:
        sections.append(overview)

    # Public Records Law Section
    if jurisdiction.level in ("s", "f") and hasattr(jurisdiction, "law"):
        law_section = _generate_law_section(jurisdiction, base_url)
        if law_section:
            sections.append(law_section)

    # Statistics Section
    if include_stats:
        stats_section = _generate_statistics_section(jurisdiction)
        if stats_section:
            sections.append(stats_section)

    # Top Agencies Section
    agencies_section = _generate_top_agencies_section(jurisdiction, base_url)
    if agencies_section:
        sections.append(agencies_section)

    # Top Localities Section (for state-level jurisdictions)
    if jurisdiction.level == "s":
        localities_section = _generate_top_localities_section(jurisdiction, base_url)
        if localities_section:
            sections.append(localities_section)

    # Recently Completed Requests Section
    if include_requests:
        requests_section = _generate_recent_requests_section(jurisdiction, base_url)
        if requests_section:
            sections.append(requests_section)

    # Additional Information Section
    additional_section = _generate_additional_info_section(jurisdiction)
    if additional_section:
        sections.append(additional_section)

    return "\n\n---\n\n".join(sections)


def _generate_header(jurisdiction, base_url=""):
    """Generate the header section with jurisdiction metadata"""
    lines = [f"# {jurisdiction.name}", ""]

    # Metadata
    metadata = []

    # Last Updated (from JurisdictionPage if available)
    if hasattr(jurisdiction, "jurisdictionpage") and jurisdiction.jurisdictionpage:
        page = jurisdiction.jurisdictionpage
        if page.updated_at:
            updated = page.updated_at.strftime("%B %d, %Y")
            metadata.append(f"**Last Updated:** {updated}")

    # Level
    level_map = {"f": "Federal", "s": "State", "l": "Local"}
    metadata.append(f"**Level:** {level_map.get(jurisdiction.level, 'Unknown')}")

    # Abbreviation
    if jurisdiction.abbrev:
        metadata.append(f"**Abbreviation:** {jurisdiction.abbrev}")

    # Parent Jurisdiction
    if jurisdiction.parent:
        parent_url = (
            base_url + jurisdiction.parent.get_absolute_url()
            if base_url
            else jurisdiction.parent.get_absolute_url()
        )
        metadata.append(
            f"**Parent Jurisdiction:** [{jurisdiction.parent.name}]({parent_url})"
        )

    lines.extend(metadata)
    return "\n".join(lines)


def _generate_overview(jurisdiction):
    """Generate the overview section with user-editable content"""
    lines = []

    # User-editable content from JurisdictionPage
    if hasattr(jurisdiction, "jurisdictionpage") and jurisdiction.jurisdictionpage:
        page = jurisdiction.jurisdictionpage
        if page.content:
            lines.append("## Overview")
            lines.append("")
            # Convert HTML to Markdown
            content_md = _html_to_markdown(page.content)
            lines.append(content_md)

    # Public notes
    if jurisdiction.public_notes:
        if not lines:
            lines.append("## Overview")
            lines.append("")
        else:
            lines.append("")
        # Convert HTML to Markdown
        notes_md = _html_to_markdown(jurisdiction.public_notes)
        lines.append(notes_md)

    return "\n".join(lines) if lines else None


def _generate_law_section(jurisdiction, base_url=""):  # pylint: disable=unused-argument
    """Generate the public records law section"""
    law = jurisdiction.law
    if not law:
        return None

    lines = ["## Public Records Law", ""]

    # Law name and shortname
    if law.shortname:
        lines.append(f"**{law.name} ({law.shortname})**")
    else:
        lines.append(f"**{law.name}**")
    lines.append("")

    # Citation with link
    lines.append(f"**Citation:** [{law.citation}]({law.url})")
    lines.append("")

    # Response deadline
    if law.days:
        day_type = "business" if law.use_business_days else "calendar"
        lines.append(f"**Response Deadline:** {law.days} {day_type} days")
    else:
        lines.append("**Response Deadline:** Not specified")
    lines.append("")

    # Appeals process
    lines.append(f"**Appeals Available:** {'Yes' if law.has_appeal else 'No'}")
    lines.append("")

    # Proxy requirement
    lines.append(f"**Proxy Required:** {'Yes' if law.requires_proxy else 'No'}")
    lines.append("")

    # Historical timeline
    if law.years.exists():
        lines.append("### Historical Timeline")
        lines.append("")
        for year in law.years.all():
            lines.append(f"- **{year.reason}:** {year.year}")
        lines.append("")

    # Coverage information
    coverage = []
    if law.cover_executive:
        coverage.append("Executive")
    if law.cover_legislative:
        coverage.append("Legislative")
    if law.cover_judicial:
        coverage.append("Judicial")

    if coverage:
        lines.append(f"**Branch Coverage:** {', '.join(coverage)}")
        lines.append("")

    # Fee & penalties information
    lines.append("### Fee & Penalties")
    lines.append("")
    lines.append(f"- **Fee Schedule:** {'Yes' if law.fee_schedule else 'No'}")
    lines.append(f"- **Penalties:** {'Yes' if law.penalties else 'No'}")
    lines.append(f"- **Trade Secrets Public:** {'Yes' if law.trade_secrets else 'No'}")
    lines.append("")

    # Law analysis
    if law.law_analysis:
        lines.append("### Law Analysis")
        lines.append("")
        # Convert HTML to Markdown
        analysis_md = _html_to_markdown(law.law_analysis)
        lines.append(analysis_md)
        lines.append("")

    return "\n".join(lines)


def _generate_statistics_section(jurisdiction):
    """Generate the statistics section with performance metrics"""
    lines = ["## Statistics", ""]

    # Gather statistics
    context = {}
    collect_stats(jurisdiction, context)

    # Performance metrics table
    lines.append("### Performance Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")

    # Total requests filed
    num_submitted = context.get("num_submitted", 0)
    lines.append(f"| Total Requests Filed | {num_submitted:,} |")

    # Allowed response time
    if jurisdiction.level in ("s", "f") and hasattr(jurisdiction, "law"):
        law = jurisdiction.law
        if law and law.days:
            day_type = "business" if law.use_business_days else "calendar"
            lines.append(f"| Allowed Response Time | {law.days} {day_type} days |")
        else:
            lines.append("| Allowed Response Time | Not specified |")
    else:
        lines.append("| Allowed Response Time | N/A |")

    # Average response time
    avg_response = jurisdiction.average_response_time()
    if avg_response > 0:
        lines.append(f"| Average Response Time | {avg_response:.1f} days |")
    else:
        lines.append("| Average Response Time | N/A |")

    # Success rate
    success = jurisdiction.success_rate()
    lines.append(f"| Success Rate | {success:.2f}% |")

    # Average fee and fee rate
    avg_fee = jurisdiction.average_fee()
    fee_rate = jurisdiction.fee_rate()
    if avg_fee > 0:
        lines.append(f"| Average Fee | ${avg_fee:.2f} |")
    else:
        lines.append("| Average Fee | $0.00 |")
    lines.append(f"| Fee Rate | {fee_rate:.2f}% |")

    # Total pages released
    total_pages = jurisdiction.total_pages()
    lines.append(f"| Total Pages Released | {total_pages:,} |")

    lines.append("")

    # Request status breakdown table
    lines.append("### Request Status Breakdown")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")

    status_labels = {
        "rejected": "Rejected",
        "ack": "Acknowledged",
        "processed": "Processed",
        "fix": "Fix Required",
        "no_docs": "No Documents",
        "done": "Completed",
        "appealing": "Appealing",
        "overdue": "Overdue",
    }

    for status_key, label in status_labels.items():
        count = context.get(f"num_{status_key}", 0)
        if count > 0:
            lines.append(f"| {label} | {count:,} |")

    lines.append("")

    return "\n".join(lines)


def _generate_top_agencies_section(jurisdiction, base_url=""):
    """Generate the top agencies section"""
    # Get top agencies
    if jurisdiction.level == "s":
        agencies = Agency.objects.filter(
            Q(jurisdiction=jurisdiction) | Q(jurisdiction__parent=jurisdiction)
        )
    else:
        agencies = jurisdiction.agencies

    agencies = (
        agencies.get_approved()
        .annotate(foia_count=Count("foiarequest", distinct=True))
        .order_by("-foia_count")[:10]
    )

    if not agencies:
        return None

    lines = ["## Top Agencies", ""]

    for i, agency in enumerate(agencies, 1):
        agency_url = (
            base_url + agency.get_absolute_url()
            if base_url
            else agency.get_absolute_url()
        )
        lines.append(
            f"{i}. [{agency.name}]({agency_url}) ({agency.foia_count:,} requests)"
        )

    return "\n".join(lines)


def _generate_top_localities_section(jurisdiction, base_url=""):
    """Generate the top localities section (for state-level jurisdictions)"""
    localities = (
        Jurisdiction.objects.filter(parent=jurisdiction)
        .annotate(foia_count=Count("agencies__foiarequest", distinct=True))
        .order_by("-foia_count")[:10]
    )

    if not localities:
        return None

    lines = ["## Top Localities", ""]

    for i, locality in enumerate(localities, 1):
        locality_url = (
            base_url + locality.get_absolute_url()
            if base_url
            else locality.get_absolute_url()
        )
        lines.append(
            f"{i}. [{locality.name}]({locality_url}) ({locality.foia_count:,} requests)"
        )

    return "\n".join(lines)


def _generate_recent_requests_section(jurisdiction, base_url=""):
    """Generate the recently completed requests section"""
    foia_requests = (
        jurisdiction.get_requests()
        .get_public()
        .get_done()
        .order_by("-datetime_done")
        .select_related("composer__user", "agency", "agency__jurisdiction")[:10]
    )

    if not foia_requests:
        return None

    lines = ["## Recently Completed Requests", ""]

    for request in foia_requests:
        # Request title (linked)
        request_url = (
            base_url + request.get_absolute_url()
            if base_url
            else request.get_absolute_url()
        )
        lines.append(f"### [{request.title}]({request_url})")
        lines.append("")

        # Requester name
        if request.composer and request.composer.user:
            user = request.composer.user
            requester_name = user.get_full_name() or user.username
        else:
            requester_name = "Unknown"
        lines.append(f"- **Requester:** {requester_name}")

        # Agency name
        lines.append(f"- **Agency:** {request.agency.name}")

        # Completion date
        if request.datetime_done:
            completed = request.datetime_done.strftime("%B %d, %Y")
            lines.append(f"- **Completed:** {completed}")

        # Number of files/documents
        file_count = (
            request.communications.aggregate(total=Count("files"))["total"] or 0
        )
        lines.append(f"- **Files:** {file_count:,}")

        lines.append("")

    return "\n".join(lines)


def _generate_additional_info_section(jurisdiction):
    """Generate the additional information section"""
    lines = []

    # Image attribution
    if jurisdiction.image_attr_line:
        if not lines:
            lines.append("## Additional Information")
            lines.append("")
        lines.append("**Image Attribution:**")
        lines.append("")
        # Convert HTML to Markdown
        attr_md = _html_to_markdown(jurisdiction.image_attr_line)
        lines.append(attr_md)
        lines.append("")

    # Holiday observation settings
    if jurisdiction.level in ("s", "f"):
        if not lines:
            lines.append("## Additional Information")
            lines.append("")
        sat_observation = (
            "Observed on Saturday" if jurisdiction.observe_sat else "Moved to Friday"
        )
        lines.append(f"**Saturday Holiday Observation:** {sat_observation}")
        lines.append("")

        # List holidays if any
        if jurisdiction.holidays.exists():
            lines.append("**Observed Holidays:**")
            lines.append("")
            for holiday in jurisdiction.holidays.all():
                lines.append(f"- {holiday.name}")
            lines.append("")

    return "\n".join(lines) if lines else None
