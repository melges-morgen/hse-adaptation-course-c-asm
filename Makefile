IMAGE := adaptation-course-tex
MAIN := adaptation_course.tex
PUD := pud_adaptation_course.tex
PRACTICE := test1_practice.tex
BUILD_DIR := build
SLIDES_IMAGE := adaptation-course-slides

.PHONY: pdf pud-pdf practice-pdf clean docker-image slides-image lecture2-slides lecture2-original lecture2 lecture3-slides lecture3

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

clean:
	rm -rf $(BUILD_DIR)
