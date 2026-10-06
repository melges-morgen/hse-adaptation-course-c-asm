IMAGE := adaptation-course-tex
MAIN := adaptation_course.tex
PUD := pud_adaptation_course.tex
PRACTICE := test1_practice.tex
BUILD_DIR := build
SLIDES_IMAGE := adaptation-course-slides
LECTURE4_IMAGE := adaptation-course-lecture04
JOURNAL_IMAGE := adaptation-course-journal
SEMINAR4_C_IMAGE := adaptation-course-seminar04-c
STAGE ?= 6

.PHONY: pdf pud-pdf practice-pdf clean docker-image slides-image lecture2-slides lecture2-original lecture2 lecture3-slides lecture3 lecture4-check lecture4-slides lecture4 lecture4-journal-check lecture4-journal-run lecture4-journal-slides lecture4-journal lecture4-quiz seminar4-factorial-check seminar4-handbook seminar4-teacher seminar4-materials seminar4 ubuntu-terminal-handbook ubuntu-terminal lab-report-handbook lab-report-check lab-report debian-install-handbook debian-install-check debian-install

docker-image:
	docker build -t $(IMAGE) .

pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		sh -c 'latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR)/latex $(MAIN) && install -Dm644 $(BUILD_DIR)/latex/adaptation_course.pdf $(BUILD_DIR)/pdf/adaptation_course.pdf'

pud-pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		sh -c 'mkdir -p $(BUILD_DIR)/latex && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR)/latex $(PUD) && install -Dm644 $(BUILD_DIR)/latex/pud_adaptation_course.pdf $(BUILD_DIR)/pdf/pud_adaptation_course.pdf'

practice-pdf: docker-image
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-w /workspace \
		$(IMAGE) \
		sh -c 'mkdir -p $(BUILD_DIR)/latex && latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR)/latex $(PRACTICE) && install -Dm644 $(BUILD_DIR)/latex/test1_practice.pdf $(BUILD_DIR)/pdf/test1_practice.pdf'

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

lecture4-quiz: docker-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace $(IMAGE) \
		sh -c 'set -e; for name in quiz-c quiz-journal teacher-key; do \
			latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=$(BUILD_DIR)/latex/lecture04-quiz assessments/lecture04/$$name.tex; \
			install -Dm644 $(BUILD_DIR)/latex/lecture04-quiz/$$name.pdf $(BUILD_DIR)/pdf/lecture04/$$name.pdf; \
		done'

seminar4-handbook: docker-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) sh scripts/build-seminar04.sh handbook

seminar4-teacher: docker-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace $(IMAGE) \
		sh -c 'sh scripts/build-tex-handbook.sh seminar04_teacher build/teacher/seminar04/guide build/pdf/teacher/seminar04/guide.pdf && sh scripts/build-tex-handbook.sh seminar04_defense build/teacher/seminar04/defense build/pdf/teacher/seminar04/defense.pdf'

seminar4-factorial-check:
	docker build -t $(SEMINAR4_C_IMAGE) demos/seminar04/factorial
	docker run --rm --cap-add SYS_PTRACE -v "$(CURDIR)":/workspace:ro -w /workspace \
		$(SEMINAR4_C_IMAGE) python3 scripts/check-seminar04-factorial.py

seminar4-materials: slides-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		--entrypoint node $(SLIDES_IMAGE) slides/materials.mjs $(BUILD_DIR) seminar04
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		--entrypoint node $(SLIDES_IMAGE) slides/materials.mjs $(BUILD_DIR) seminar04/factorial

seminar4: pdf seminar4-handbook seminar4-materials seminar4-factorial-check
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) python3 scripts/check-seminar04-handbook.py $(BUILD_DIR)

ubuntu-terminal-handbook: docker-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) sh scripts/build-ubuntu-terminal.sh handbook

ubuntu-terminal: pdf ubuntu-terminal-handbook
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) python3 scripts/check-ubuntu-terminal.py $(BUILD_DIR)

lab-report-handbook: docker-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) sh scripts/build-lab-report.sh handbook

lab-report-check:
	docker build -t $(SEMINAR4_C_IMAGE) demos/seminar04/factorial
	docker run --rm --cap-add SYS_PTRACE -v "$(CURDIR)":/workspace:ro -w /workspace \
		$(SEMINAR4_C_IMAGE) python3 scripts/check-demo-lab.py

lab-report: pdf lab-report-handbook lab-report-check
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) python3 scripts/check-demo-lab-handbook.py $(BUILD_DIR)

debian-install-handbook: docker-image
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) sh scripts/build-debian-install.sh handbook

debian-install-check:
	docker build -t $(SEMINAR4_C_IMAGE) demos/seminar04/factorial
	docker run --rm -v "$(CURDIR)":/workspace:ro -w /workspace \
		$(SEMINAR4_C_IMAGE) python3 scripts/check-debian-install.py

debian-install: pdf debian-install-handbook debian-install-check
	docker run --rm -v "$(CURDIR)":/workspace -w /workspace \
		$(IMAGE) python3 scripts/check-debian-install-handbook.py $(BUILD_DIR)

clean:
	rm -rf $(BUILD_DIR)
