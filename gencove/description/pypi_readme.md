# The Gencove CLI

[![PyPI Latest Release](https://img.shields.io/pypi/v/gencove.svg)](https://pypi.org/project/gencove/)
[![License](https://img.shields.io/pypi/l/gencove.svg)](https://github.com/gncv/gencove-cli/blob/master/LICENSE)

## What is Gencove?

Gencove is a high-throughput, cost-effective platform for genome sequencing and analysis, enabling a wide array of genomics applications across industries. Furthermore, it is the only enterprise analytics platform for low-pass whole genome sequencing (lpWGS).


The Gencove command-line interface (CLI) can be used to easily access the Gencove platform.

## Main Features

It is most often used for:
* [Uploading FASTQ files](https://docs.gencove.com/base/analysis/fastq-files/uploading-using-the-cli/) for analysis
* [Downloading analysis results](https://docs.gencove.com/base/analysis/samples/downloading-deliverables/) which include the following:
  * Sequence (`.fastq.gz`)
  * Alignment (`.bam`, `.bai`)
  * Imputation (`.vcf.gz`, `.vcf.gz.tbi`, `.vcf.gz.csi`)
* [Assigning metadata](https://docs.gencove.com/base/analysis/samples/sample-metadata-and-files/#assigning-sample-metadata) to Gencove samples

Before filing a bug report, please refer to the following [link](https://docs.gencove.com/general/support/#filing-a-bug-report-for-the-cli). Bugs should be reported [here](https://resources.gencove.com/hc/en-us/requests/new).

## Installation
```
# install via PyPI
pip install gencove

# updating to latest version
pip install -U gencove
```

## Documentation

Online documentation (with examples) is available at [docs.gencove.com](https://docs.gencove.com/base/getting-started/)

API reference for publicly available endpoints: [API Reference](https://api.gencove.com/api/v2/docs/)

Comprehensive CLI Documentation available: [CLI Reference](https://docs.gencove.com/base/cli-reference/)
