# Narrative Time

First timeline-based annotation framework that achieves full coverage of all possible TLINKS.

## Repository structure:

- annotationTool: contains the annotation tool. Just open `AnnotationTool.html` in your browser.
- corpus: contains NarrativeTime-annotated TimeBank corpus
  - nt_format: output of the annotation tool in NarrativeTime format. If the file ends with `_tml`, it has extra TimeBank metadata.
  - nt_converted_to_tml: NarrativeTime format converted to TML format using `utils/nt2tml.py`
- narrative_time: contains the NarrativeTime package, it is a Python package that can be installed using `pip install -e .`. It contains useful functions to work with NarrativeTime format.
- notebooks: contains Jupyter notebooks with EDA, agreement computation and modeling
- utils: contains conversion script and a script to add metadata to NarrativeTime format

## Conversion to TML format

Annotation tool output can be converted to TML format using `utils/nt2tml.py` script. Usage example:

```bash
python narrative_time/nt2tml.py \
    --input_file corpus/timebank/nt_format/tbd_a1_tml.jsonl \
    --output_dir corpus/timeml_converted/a1
```

nt2tml.py is a command line tool that converts data in the NarrativeTime format (a jsonl file) to the TimeML format (a set of xml files) and saves the xml files to the specified output directory.

The tool has several optional arguments that allow the user to customize the conversion process:

* `--verbocity`: Controls the level of output that the tool prints. With a value of 0, no output is printed. With a value of 1, only the final results are printed. With a value of 2, all intermediate steps are printed as well.
* `--add_narrative_time_info`: If this flag is present, the tool will add additional NarrativeTime tags to the output xml files. This can be useful for debugging or for making the xml files more readable. This flag does not affect tlinks, only the NarrativeTime tags.
* `--do_not_use_global_eiid`: If this flag is present, the tool will always generate new eiids (event instance IDs) starting from 0, rather than using a global counter. This can be useful for testing.
