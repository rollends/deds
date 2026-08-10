BUILDDIRECTORY := .build
DOCUMENTS      := dfl-conf-paper.pdf dfl-conf-paper-slides.pdf
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

DFLCONFPAPER_SLIDES 		:= dfl-conf-paper-slides.pdf
DFLCONFPAPERSOURCE_SLIDES	:= dfl-conf-paper-slides.tex
DFLCONFPAPERDEPENDS_SLIDES	:= dflconfbib.bib figures.sty notation.sty figures/example-2-pure-search.pdf figures/example-2-pure-search-answer.png figures/cat-sad-1.png figures/nod.png figures/bellman.jpg
$(DFLCONFPAPER_SLIDES): $(DFLCONFPAPERSOURCE_SLIDES) $(DFLCONFPAPERDEPENDS_SLIDES)
	mkdir -p $(BUILDDIRECTORY)/$@/
	cp $^ $(BUILDDIRECTORY)/$@/
	mv $(BUILDDIRECTORY)/$@/$(DFLCONFPAPERSOURCE_SLIDES) $(BUILDDIRECTORY)/$@/root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) -jobname=$(basename $@) root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) -jobname=$(basename $@) root.tex
	cd $(BUILDDIRECTORY)/$@/ && $(TEXFOT) $(XELATEX) -jobname=$(basename $@) root.tex
	cp $(BUILDDIRECTORY)/$@/$@ $@

figures/%.png: figures/%.gif figures/%.gif.frame
	convert figures/$*.gif -coalesce \( -clone $(shell cat figures/$*.gif.frame) -write $@ \) null:

figures/%: figures/%.url
	curl -f -o $@ `cat $<`

submission-$(DFLCONFPAPER): $(BUILDDIRECTORY)/$(DFLCONFPAPER)/root.zip

spellcheck-$(DFLCONFPAPER): $(BUILDDIRECTORY)/$(DFLCONFPAPER)/spellcheck.txt

spellcheck-$(DFLCONFPAPER_SLIDES): $(BUILDDIRECTORY)/$(DFLCONFPAPER_SLIDES)/spellcheck.txt

$(BUILDDIRECTORY)/$(DFLCONFPAPER)/root.zip: $(DFLCONFPAPER)
	cd $(BUILDDIRECTORY)/$(DFLCONFPAPER)/ && zip root.zip root.tex $(DFLCONFPAPERDEPENDS)

$(BUILDDIRECTORY)/$(DFLCONFPAPER)/spellcheck.txt: $(DFLCONFPAPER)
	cd $(BUILDDIRECTORY)/$(DFLCONFPAPER)/ && hunspell -l -t root.tex > spellcheck.txt

$(BUILDDIRECTORY)/$(DFLCONFPAPER_SLIDES)/spellcheck.txt: $(DFLCONFPAPER_SLIDES)
	cd $(BUILDDIRECTORY)/$(DFLCONFPAPER_SLIDES)/ && hunspell -l -t root.tex > spellcheck.txt

submission: submission-$(DFLCONFPAPER)

spellcheck: spellcheck-$(DFLCONFPAPER) spellcheck-$(DFLCONFPAPER_SLIDES)


.PHONY: all clean package spellcheck submission submission-$(DFLCONFPAPER)
