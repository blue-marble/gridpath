# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = python -msphinx
SPHINXPROJ    = GridPath
SOURCEDIR     = source
BUILDDIR      = build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile img_gen

graphics/optype_opchar_matrix.svg graphics/optype_opchar_matrix.png: ../gridpath/project/operations/operational_types/opchar_param_requirements.csv
	@python opchar_img_gen.py

# Eliminates the circular dependency caused by the catch-all target
../gridpath/project/operations/operational_types/opchar_param_requirements.csv: ;

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile graphics/optype_opchar_matrix.svg graphics/optype_opchar_matrix.png
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	

