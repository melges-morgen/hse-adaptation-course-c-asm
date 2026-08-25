IMAGE := adaptation-course-tex
MAIN := adaptation_course.tex
BUILD_DIR := build

.PHONY: pdf clean docker-image

docker-image:
	docker build -t $(IMAGE) .

pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR) $(MAIN)

clean:
	rm -rf $(BUILD_DIR)
