import csv
from typing import Tuple, Dict
from esco.ESCODBHandler import ESCODBHandler as DBHandler
from pathlib import Path


class ESCODatasetParser:
    """Parser to read ESCO v1.2.0 CSV data and insert into a normalized schema"""

    # Files to import in FK-dependency order
    IMPORT_ORDER = [
        "ISCOGroups_en.csv",
        "occupations_en.csv",
        "skillGroups_en.csv",
        "skills_en.csv",
        "occupationSkillRelations_en.csv",
        "broaderRelationsOccPillar_en.csv",
        "broaderRelationsSkillPillar_en.csv",
        "skillSkillRelations_en.csv",
        "greenShareOcc_en.csv",
    ]

    SKILL_COLLECTION_FILES = {
        "digitalSkillsCollection_en.csv":     "digital",
        "greenSkillsCollection_en.csv":       "green",
        "digCompSkillsCollection_en.csv":     "digComp",
        "languageSkillsCollection_en.csv":    "language",
        "transversalSkillsCollection_en.csv": "transversal",
        "researchSkillsCollection_en.csv":    "research_skills",
    }

    OCCUPATION_COLLECTION_FILES = {
        "researchOccupationsCollection_en.csv": "research_occupations",
    }

    def __init__(self, db_handler: DBHandler, dataset_dir=None):
        self.db_handler: DBHandler = db_handler
        self.dataset_dir = Path(dataset_dir) if dataset_dir is not None else None  # FIXED: cast to Path

    # ------------------------------------------------------------------
    # Validation / setup
    # ------------------------------------------------------------------

    def validate_folder(self) -> None:
        if not self.dataset_dir.exists():
            raise FileNotFoundError(f"ESCO folder not found: {self.dataset_dir}")

        required_files = {"occupations_en.csv", "skills_en.csv", "occupationSkillRelations_en.csv"}
        found_files = {f.name for f in self.dataset_dir.glob("*.csv")}
        missing = required_files - found_files

        if missing:
            raise ValueError(
                f"ESCO folder missing required files: {missing}\n"
                f"Found: {found_files}"
            )

    def ensure_dataset(self) -> bool:
        if self.dataset_dir.exists():
            print(f"✓ Found ESCO folder at: {self.dataset_dir}")
            return True
        else:
            raise FileNotFoundError(
                f"ESCO folder not found: {self.dataset_dir}"
            )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def parse_dataset(self) -> Tuple[int, int]:
        self.ensure_dataset()
        self.validate_folder()

        successful = 0
        failed = 0

        print(f"\nParsing ESCO dataset: {self.dataset_dir}")
        print("-" * 50)

        # --- Main files (ordered by FK dependencies) ---
        for filename in self.IMPORT_ORDER:
            filepath = self.dataset_dir / filename
            if not filepath.exists():
                print(f"  ⚠ Skipping missing file: {filename}")
                continue

            print(f"\n  📥 Importing: {filename}")
            ok, err = self._import_file(filepath, filename)
            successful += ok
            failed += err

        # --- Skill collection files ---
        for filename, collection_name in self.SKILL_COLLECTION_FILES.items():
            filepath = self.dataset_dir / filename
            if not filepath.exists():
                print(f"  ⚠ Skipping missing collection: {filename}")
                continue

            print(f"\n  📥 Importing skill collection [{collection_name}]: {filename}")
            ok, err = self._import_skill_collection(filepath, collection_name)
            successful += ok
            failed += err

        # --- Occupation collection files ---
        for filename, collection_name in self.OCCUPATION_COLLECTION_FILES.items():
            filepath = self.dataset_dir / filename
            if not filepath.exists():
                print(f"  ⚠ Skipping missing collection: {filename}")
                continue

            print(f"\n  📥 Importing occupation collection [{collection_name}]: {filename}")
            ok, err = self._import_occupation_collection(filepath, collection_name)
            successful += ok
            failed += err

        print("\n" + "-" * 50)
        print("\n✓ Import complete!")
        print(f"  Successful: {successful}")
        print(f"  Failed:     {failed}")
        print(f"  Total:      {successful + failed}")

        return successful, failed

    # ------------------------------------------------------------------
    # Routing
    # ------------------------------------------------------------------

    def _import_file(self, filepath: Path, filename: str) -> Tuple[int, int]:
        routes = {
            "ISCOGroups_en.csv":                  self._import_isco_groups,
            "occupations_en.csv":                 self._import_occupations,
            "skillGroups_en.csv":                 self._import_skill_groups,
            "skills_en.csv":                      self._import_skills,
            "occupationSkillRelations_en.csv":    self._import_occ_skill_relations,
            "broaderRelationsOccPillar_en.csv":   self._import_broader_occ,   
            "broaderRelationsSkillPillar_en.csv": self._import_broader_skill,  
            "skillSkillRelations_en.csv":         self._import_skill_skill_relations,
            # "greenShareOcc_en.csv":             self._import_green_share,   
        }
        method = routes.get(filename)
        if method is None:
            print(f"    ⚠ No import method for: {filename}")
            return 0, 0
        return method(filepath)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _or_none(value: str):
        """Return None for empty/whitespace strings, otherwise the stripped value"""
        if value is None:
            return None
        v = value.strip()
        return v if v else None

    @staticmethod
    def _clean_row(row: dict) -> dict:
        """Strip whitespace from dict keys (some CSVs have padded headers)"""
        return {k.strip(): v for k, v in row.items()}

    # ------------------------------------------------------------------
    # Entity importers
    # ------------------------------------------------------------------

    def _import_isco_groups(self, filepath: Path) -> Tuple[int, int]:
        successful = 0
        failed = 0

        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("conceptUri", "")
                id = row.get("code", "")

                if self.db_handler.insert_isco_group(
                    id=id,
                    url=url,
                    preferred_label=row.get("preferredLabel", ""),
                    status=row.get("status", ""),
                    alt_labels=row.get("altLabels", ""),
                    description=row.get("description", ""),
                ):
                    successful += 1
                else:
                    failed += 1

        print(f"    Loaded {successful} ISCO groups")
        return successful, failed

    def _import_occupations(self, filepath: Path) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("conceptUri", "")
                isco_group_id = row.get("iscoGroup", "").strip()

                if self.db_handler.insert_occupation(
                    url=url,
                    preferred_label=row.get("preferredLabel", ""),
                    alt_labels=row.get("altLabels", ""),
                    hidden_labels=row.get("hiddenLabels", ""),
                    status=row.get("status", ""),
                    modified_date=self._or_none(row.get("modifiedDate", "")),
                    isco_group_id=isco_group_id,
                    regulated_profession_note=row.get("regulatedProfessionNote", ""),
                    scope_note=row.get("scopeNote", ""),
                    definition=row.get("definition", ""),
                    description=row.get("description", ""),
                    code=row.get("code", ""),
                    nace_code=row.get("naceCode", ""),
                ):
                    successful += 1
                    if successful % 1000 == 0:
                        print(f"    Processed {successful} occupations...")
                else:
                    failed += 1
        return successful, failed

    def _import_skill_groups(self, filepath: Path) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("conceptUri", "")

                if self.db_handler.insert_skill_group(
                    url=url,
                    preferred_label=row.get("preferredLabel", ""),
                    alt_labels=row.get("altLabels", ""),
                    hidden_labels=row.get("hiddenLabels", ""),
                    status=row.get("status", ""),
                    modified_date=self._or_none(row.get("modifiedDate", "")),
                    scope_note=row.get("scopeNote", ""),
                    description=row.get("description", ""),
                    code=row.get("code", ""),
                ):
                    successful += 1
                else:
                    failed += 1
        print(f"    Loaded {successful} skill groups")
        return successful, failed

    def _import_skills(self, filepath: Path) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("conceptUri", "")

                if self.db_handler.insert_skill(
                    url=url,
                    type=self._or_none(row.get("skillType", "")),
                    reuse_level=self._or_none(row.get("reuseLevel", "")),
                    preferred_label=row.get("preferredLabel", ""),
                    alt_labels=row.get("altLabels", ""),
                    hidden_labels=row.get("hiddenLabels", ""),
                    status=row.get("status", ""),
                    modified_date=self._or_none(row.get("modifiedDate", "")),
                    scope_note=row.get("scopeNote", ""),
                    definition=row.get("definition", ""),
                    description=row.get("description", ""),
                ):
                    successful += 1
                    if successful % 1000 == 0:
                        print(f"    Processed {successful} skills...")
                else:
                    failed += 1
        return successful, failed

    # ------------------------------------------------------------------
    # Relationship importers
    # ------------------------------------------------------------------

    def _import_occ_skill_relations(self, filepath: Path) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if self.db_handler.insert_occ_skill_relation(
                    occupation_url=row.get("occupationUri", ""),
                    skill_url=row.get("skillUri", ""),
                    type=row.get("relationType", ""),
                ):
                    successful += 1
                    if successful % 5000 == 0:
                        print(f"    Processed {successful} occ-skill relations...")
                else:
                    failed += 1
        return successful, failed

    def _import_broader_occ(self, filepath: Path) -> Tuple[int, int]:
        """Route broader occupation pillar rows by type:
        - ISCOGroup → ISCOGroup: update isco_groups.broader_isco_group_id
        - Occupation → Occupation: insert into occupation_broader (by id)
        - Occupation → ISCOGroup: skip (already in occupations.isco_group_id)
        """
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                concept_type = row.get("conceptType", "").strip()
                concept_url = row.get("conceptUri", "").strip()
                broader_type = row.get("broaderType", "").strip()
                broader_url = row.get("broaderUri", "").strip()

                if not concept_url or not broader_url or concept_url == broader_url:
                    continue

                ok = False
                if concept_type == "ISCOGroup" and broader_type == "ISCOGroup":
                    ok = self.db_handler.update_isco_broader(concept_url, broader_url)
                elif concept_type == "Occupation" and broader_type == "Occupation":
                    ok = self.db_handler.insert_occupation_broader(concept_url, broader_url)
                elif concept_type == "Occupation" and broader_type == "ISCOGroup":
                    ok = True  # Already captured by occupations.isco_group_id
                else:
                    print(f"    ⚠ Unexpected broader occ types: {concept_type} → {broader_type}")
                    ok = True  # don't count as failure

                if ok:
                    successful += 1
                else:
                    failed += 1

        print(f"    Processed {successful} broader occupation relations")
        return successful, failed

    def _import_broader_skill(self, filepath: Path) -> Tuple[int, int]:
        """Route broader skill pillar rows by type:
        - SkillGroup → SkillGroup: update skill_groups.broader_skill_group_id
        - KnowledgeSkillCompetence → SkillGroup: insert into skill_broader_groups (by id)
        - KnowledgeSkillCompetence → KnowledgeSkillCompetence: insert into skill_broader (by id)
        """
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                concept_type = row.get("conceptType", "").strip()
                concept_url = row.get("conceptUri", "").strip()
                broader_type = row.get("broaderType", "").strip()
                broader_url = row.get("broaderUri", "").strip()

                if not concept_url or not broader_url or concept_url == broader_url:
                    continue

                ok = False
                if concept_type == "SkillGroup" and broader_type == "SkillGroup":
                    ok = self.db_handler.update_skill_group_broader(concept_url, broader_url)
                elif concept_type == "KnowledgeSkillCompetence" and broader_type == "SkillGroup":
                    ok = self.db_handler.insert_skill_broader_group(concept_url, broader_url)
                elif concept_type == "KnowledgeSkillCompetence" and broader_type == "KnowledgeSkillCompetence":  
                    ok = self.db_handler.insert_skill_broader(concept_url, broader_url)                          
                else:
                    print(f"    ⚠ Unexpected broader skill types: {concept_type} → {broader_type}")
                    ok = True

                if ok:
                    successful += 1
                    if successful % 5000 == 0:
                        print(f"    Processed {successful} broader skill relations...")
                else:
                    failed += 1

        print(f"    Processed {successful} broader skill relations")
        return successful, failed

    def _import_skill_skill_relations(self, filepath: Path) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if self.db_handler.insert_skill_skill_relation(
                    original_skill_url=row.get("originalSkillUri", ""),
                    related_skill_url=row.get("relatedSkillUri", ""),
                    type=self._or_none(row.get("relationType", "")),
                ):
                    successful += 1
                    if successful % 5000 == 0:
                        print(f"    Processed {successful} skill-skill relations...")
                else:
                    failed += 1
        return successful, failed

    # ------------------------------------------------------------------
    # Green share importer
    # ------------------------------------------------------------------

    def _import_green_share(self, filepath: Path) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                concept_type = row.get("conceptType", "").strip()
                url = row.get("conceptUri", "").strip()
                green_share = row.get("greenShare", "").strip()

                if not url or not green_share:
                    continue

                green_val = float(green_share)

                if concept_type == "Occupation":
                    table = "occupations"
                elif concept_type == "ISCOGroup":
                    table = "isco_groups"
                else:
                    print(f"    ⚠ Unexpected green share type: {concept_type}")
                    continue

                if self.db_handler.update_green_share(url, green_val, table):
                    successful += 1
                else:
                    failed += 1

        print(f"    Updated {successful} green share values")
        return successful, failed

    # ------------------------------------------------------------------
    # Collection importers
    # ------------------------------------------------------------------

    def _import_skill_collection(self, filepath: Path, collection_name: str) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("conceptUri", "").strip()
                if not url:
                    continue
                if self.db_handler.insert_skill_collection_member(collection_name, url):
                    successful += 1
                else:
                    failed += 1
        print(f"    Loaded {successful} members into [{collection_name}]")
        return successful, failed

    def _import_occupation_collection(self, filepath: Path, collection_name: str) -> Tuple[int, int]:
        successful = 0
        failed = 0
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row.get("conceptUri", "").strip()
                if not url:
                    continue
                if self.db_handler.insert_occupation_collection_member(collection_name, url):
                    successful += 1
                else:
                    failed += 1
        print(f"    Loaded {successful} members into [{collection_name}]")
        return successful, failed