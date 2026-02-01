BUILDDIRECTORY := .build
DOCUMENTS      := dfl-conf-paper.pdf
TEX_OPTIONS    := -no-shell-escape -interaction=nonstopmode -file-line-error -halt-on-error
PDFLATEX       := pdflatex $(TEX_OPTIONS)
XELATEX        := xelatex $(TEX_OPTIONS)
TEXFOT         := texfot
BIBTEX         := bibtex
BIBER          := biber
FIGURESNAMES   := 
PDFFIGURES     := $(addprefix figures/,$(addsuffix .pdf, $(FIGURESNAMES)))

all: $(DOCUMENTS)

clean:
	rm -rf $(BUILDDIRECTORY) $(DOCUMENTS)

DFLCONFPAPER 		:= dfl-conf-paper.pdf
DFLCONFPAPERSOURCE  := dfl-conf-paper.tex
DFLCONFPAPERDEPENDS := ifacconf.cls ifacconf.bst dflconfbib.bib figures.sty notation.sty
$(DFLCONFPAPER): $(DFLCONFPAPERSOURCE) $(DFLCONFPAPERDEPENDS)
	mkdir -p $(BUILDDIRECTORY)/$@/
	cp $^ $(BUILDDIRECTORY)/$@/
	mv $(BUILDDIRECTORY)/$@/$(DFLCONFPAPERSOURCE) $(BUILDDIRECTORY)/$@/root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) -jobname=$(basename $@) root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(BIBTEX) $(basename $@)
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) -jobname=$(basename $@) root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) -jobname=$(basename $@) root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) -jobname=$(basename $@) root.tex
	cp $(BUILDDIRECTORY)/$@/$@ $@

submission-$(DFLCONFPAPER): $(BUILDDIRECTORY)/$(DFLCONFPAPER)/root.zip

spellcheck-$(DFLCONFPAPER): $(BUILDDIRECTORY)/$(DFLCONFPAPER)/spellcheck.txt

$(BUILDDIRECTORY)/$(DFLCONFPAPER)/root.zip: $(DFLCONFPAPER)
	cd $(BUILDDIRECTORY)/$(DFLCONFPAPER)/ && zip root.zip root.tex $(DFLCONFPAPERDEPENDS)

$(BUILDDIRECTORY)/$(DFLCONFPAPER)/spellcheck.txt: $(DFLCONFPAPER)
	cd $(BUILDDIRECTORY)/$(DFLCONFPAPER)/ && hunspell -l -t root.tex > spellcheck.txt

submission: submission-$(DFLCONFPAPER)

spellcheck: spellcheck-$(DFLCONFPAPER)


.PHONY: all clean package spellcheck submission submission-$(DFLCONFPAPER)
