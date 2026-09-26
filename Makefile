IMAGE := adaptation-course-tex
MAIN := adaptation_course.tex
PUD := pud_adaptation_course.tex
PRACTICE := test1_practice.tex
BUILD_DIR := build
SLIDES_IMAGE := adaptation-course-slides
LECTURE4_IMAGE := adaptation-course-lecture04
JOURNAL_IMAGE := adaptation-course-journal
STAGE ?= 6

.PHONY: pdf pud-pdf practice-pdf clean docker-image slides-image lecture2-slides lecture2-original lecture2 lecture3-slides lecture3 lecture4-check lecture4-slides lecture4 lecture4-journal-check lecture4-journal-run lecture4-journal-slides lecture4-journal

docker-image:
	docker build -t $(IMAGE) .

pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(MAIN)

pud-pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(PUD)

practice-pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(PRACTICE)

slides-image:
	docker build -t $(SLIDES_IMAGE) slides

lecture2-slides: slides-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(SLIDES_IMAGE) $(BUILD_DIR)
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		--entrypoint node $(SLIDES_IMAGE) slides/check-artifacts.mjs $(BUILD_DIR)

lecture2: pdf lecture2-slides

lecture2-original: slides-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(SLIDES_IMAGE) $(BUILD_DIR) lecture02-original
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		--entrypoint node $(SLIDES_IMAGE) slides/check-artifacts.mjs $(BUILD_DIR) lecture02-original

lecture3-slides: slides-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(SLIDES_IMAGE) $(BUILD_DIR) lecture03
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		--entrypoint node $(SLIDES_IMAGE) slides/check-artifacts.mjs $(BUILD_DIR) lecture03

lecture3: pdf lecture3-slides

lecture4-check:
	python3 scripts/check-lecture04.py
	docker build --platform linux/amd64 -t $(LECTURE4_IMAGE) demos/lecture04
	docker run --rm --platform linux/amd64 -v "$(CURDIR)":/workspace:ro \
		-w /workspace $(LECTURE4_IMAGE)

lecture4-slides: slides-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(SLIDES_IMAGE) $(BUILD_DIR) lecture04
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		--entrypoint node $(SLIDES_IMAGE) slides/check-artifacts.mjs $(BUILD_DIR) lecture04

lecture4: pdf lecture4-check lecture4-slides

lecture4-journal-check:
	docker build -t $(JOURNAL_IMAGE) demos/lecture04-journal
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace $(JOURNAL_IMAGE) \
		sh -c 'set -e; for stage in 1 2 3 4 5 6; do sh demos/lecture04-journal/build.sh "$$stage"; done; python3 demos/lecture04-journal/check.py'

lecture4-journal-run:
	docker build -t $(JOURNAL_IMAGE) demos/lecture04-journal
	docker run --rm -it -p 127.0.0.1:6080:6080 -v "$(CURDIR)":/workspace \
		-w /workspace $(JOURNAL_IMAGE) sh demos/lecture04-journal/run.sh $(STAGE)

lecture4-journal-slides: slides-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(SLIDES_IMAGE) $(BUILD_DIR) lecture04-journal
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		--entrypoint node $(SLIDES_IMAGE) slides/check-artifacts.mjs $(BUILD_DIR) lecture04-journal

lecture4-journal: pdf lecture4-journal-check lecture4-journal-slides

clean:
	rm -rf $(BUILD_DIR)
