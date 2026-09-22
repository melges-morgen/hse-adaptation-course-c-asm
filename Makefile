IMAGE := adaptation-course-tex
MAIN := adaptation_course.tex
PRACTICE := test1_practice.tex
BUILD_DIR := build

.PHONY: pdf practice-pdf clean docker-image

docker-image:
	docker build -t $(IMAGE) .

pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(MAIN)

practice-pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(PRACTICE)

clean:
	rm -rf $(BUILD_DIR)
