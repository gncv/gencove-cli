"""Utilities for listing merged VCF files."""

from gencove.models import ProjectMergeVCFs


def get_line(merged_vcf):
    """Build a list of relevant data to be printed.

    Args:
        merged_vcf (dict): an object from project merge VCF response

    Returns:
        str: tab delimited list of relevant data to be printed
    """
    if isinstance(merged_vcf, ProjectMergeVCFs):
        return "\t".join(
            [
                str(merged_vcf.id),
                merged_vcf.last_status.created.isoformat(),
                merged_vcf.last_status.status,
            ]
        )
    return "\t".join(
        [
            merged_vcf["id"],
            merged_vcf["last_status"]["created"],
            merged_vcf["last_status"]["status"],
        ]
    )
