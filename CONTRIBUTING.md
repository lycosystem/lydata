# Working with us on the lyDATA Project

There are two main contributions you can make to the project:

1. You work at an institution that treats patients and you want to contribute a dataset to our repository. In that case, stay here and read on.
2. You have some Python skills and want to contribute to the [little Python library] that we wrote as an interface to the data. If that applies to you, then follow [these general guidelines] on how we write, test, document, and publish our Python packages.

[little Python library]: https://github.com/lycosystem/lydata-package
[these general guidelines]: https://github.com/lycosystem/.github/wiki

## Adding a new Dataset to the Collection

If you have patient records of a cohort of patients that were newly diagnosed with HNSCC, then you may be able to help us and other researchers by sharing the patterns of lymphatic progression these patients exhibited.

> [!WARNING]
> Contact us (e.g. <yoel.perezhaas@usz.ch>, or <noemi.buehrer@usz.ch>). This should always be your first step, before you prepare any data, so we can make sure the data fits our effort and you don't waste precious time.

> [!CAUTION]
> It is easy to accidentally publish sensitive patient information. If you are a collaborator, make sure that whatever you send us is already fully anonymized. If you are a maintainer of this repository, make sure you don't commit any sensitive information. And if you did commit it to the private part of the repo, make sure you **squash the commit history before merging** it into the public part of the repo.

Check in what format your records are available/exportable. Depending on that, there are two option:

1. If they are still in some hospital database and you need to extract them into a table, then please use our CSV format. For an example, you may look at [this dataset and its documentation]. Inside, you'll find a `README.md` that describes its columns and a `data.csv` with the full table. Use this as a template and add one row per patient. You could also try [our experimental GUI] for collecting the data into the right format.
2. When you have already collected the information into an Excel or CSV table, then you can just send it to us and we convert it into our format (feel free to try it yourself using our [conversion CLI tool]). In that case, we'll place the data you sent us in there as `raw.csv`. See our [first external contribution] for an example.

[this dataset and its documentation]: https://github.com/lycosystem/lydata/tree/main/2021-usz-oropharynx
[our experimental GUI]: https://lyscripts.readthedocs.io/latest/data/collect.html
[conversion CLI tool]: https://lyscripts.readthedocs.io/latest/data/lyproxify.html
[first external contribution]: https://github.com/lycosystem/lydata/tree/main/2021-clb-oropharynx

## Reproducibility and Traceability

We try to make everything about the data as transparent as possible. This is why we often include the `raw.csv` file that we got from the contributor and define a script (in the `scripts/` directory) and/or a command in the [`dvc.yaml`] pipeline definition that converts the `raw.csv` into the final `data.csv` that can be found in every dataset's subdirectory.

This ensures that potential errors in the data can be traced back to either our processing pipeline or the original data as provided by the contributor. It also allows us to update the data in the future while being transparent about the changes made (although in practice that may be hidden in the git history).

To reproduce all the steps defined in the [`dvc.yaml`] file, follow these steps:

1. Make sure you have [uv installed].
2. Clone the repository and navigate to the dataset's directory:

   ```bash
   git clone https://github.com/lycosystem/lydata
   cd lydata
   ```

3. Run the [dvc] command via [`uvx`]:

   ```bash
   uvx dvc repro
   ```

> [!NOTE]
> You do not need to create a virtual environment or install dependencies. Every Python script in the `scripts/` directory contains inline metadata per [PEP723] that defines the dependencies required to run it. And since every scripts is called by [`uv run`], which is [PEP723] compatible, it will automatically run every script in its own virtual environment with the required dependencies installed.
>
> Also, most calls to `lyscripts data lyproxify` command use their own set of dependencies defined in the respective data folder's `requirements.in` files.
>
> The reason for this "containerized" setup is that these scripts are added over time and we don't want to update every scripts whenever we want to write a new script that depends on a newer version of e.g. `numpy`. Also, these scripts are not meant to be reused.

[`dvc.yaml`]: https://dvc.org/doc/user-guide/project-structure/dvcyaml-files#dvcyaml
[uv installed]: https://docs.astral.sh/uv/getting-started/installation/
[dvc]: https://dvc.org/doc/
[`uvx`]: https://docs.astral.sh/uv/guides/tools/
[PEP723]: https://packaging.python.org/en/latest/specifications/inline-script-metadata/
[`uv run`]: https://docs.astral.sh/uv/guides/scripts/
