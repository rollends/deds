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


# DFLPAPERDEPENDS := autart.cls notation.sty
# dfl-paper.pdf: dfl-paper.tex $(DFLPAPERDEPENDS)
# 	mkdir -p $(BUILDDIRECTORY)/$@/
# 	cp $^ $(BUILDDIRECTORY)/$@/
# 	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(PDFLATEX) dfl-paper.tex
# #	cd $(BUILDDIRECTORY)/$@/ && $(BIBER) confpaper
# 	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(PDFLATEX) dfl-paper.tex
# 	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(PDFLATEX) dfl-paper.tex
# 	cp $(BUILDDIRECTORY)/$@/$@ $@

DFLCONFPAPERDEPENDS := ifacconf.cls ifacconf.bst dflconfbib.bib figures.sty notation.sty
dfl-conf-paper.pdf: dfl-conf-paper.tex $(DFLCONFPAPERDEPENDS)
	mkdir -p $(BUILDDIRECTORY)/$@/
	cp $^ $(BUILDDIRECTORY)/$@/
	cp $(BUILDDIRECTORY)/$@/dfl-conf-paper.tex $(BUILDDIRECTORY)/$@/root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) dfl-conf-paper.tex
	cd $(BUILDDIRECTORY)/$@/ && $(BIBTEX) dfl-conf-paper
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) dfl-conf-paper.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) dfl-conf-paper.tex
	cp $(BUILDDIRECTORY)/$@/$@ $@

submission: submission-dfl-conf-paper.pdf.zip

submission-dfl-conf-paper.pdf.zip: dfl-conf-paper.pdf
	cd $(BUILDDIRECTORY)/dfl-conf-paper.pdf/ && zip $@ root.tex $(DFLCONFPAPERDEPENDS)
	cp $(BUILDDIRECTORY)/dfl-conf-paper.pdf/$@ $@

spellcheck: spellcheck-dfl-conf-paper


spellcheck-%: %.tex
	hunspell -l -t $*.tex > $@


.PHONY: all clean package spellcheck submission
