"""Unit tests for Template Marketplace."""

import json
from pathlib import Path

import pytest

from cli.commands.templates import TemplateMarketplace, TemplateMetadata


class TestTemplateMetadata:
    """Test TemplateMetadata class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        metadata = TemplateMetadata(
            name="test_template", description="Test", category="professional"
        )

        assert metadata.name == "test_template"
        assert metadata.description == "Test"
        assert metadata.category == "professional"
        assert metadata.author == "unknown"
        assert metadata.version == "1.0.0"
        assert metadata.tags == []
        assert metadata.formats == ["md", "tex", "pdf"]
        assert metadata.rating == 0.0
        assert metadata.reviews_count == 0
        assert metadata.downloads == 0
        assert metadata.source == "local"

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        metadata = TemplateMetadata(
            name="custom_template",
            description="Custom template",
            category="modern",
            author="test_user",
            version="2.0.0",
            tags=["custom", "modern"],
            formats=["md"],
            rating=4.5,
            reviews_count=10,
            downloads=100,
            source="user",
        )

        assert metadata.name == "custom_template"
        assert metadata.author == "test_user"
        assert metadata.version == "2.0.0"
        assert metadata.tags == ["custom", "modern"]
        assert metadata.formats == ["md"]
        assert metadata.rating == 4.5
        assert metadata.reviews_count == 10
        assert metadata.downloads == 100

    def test_to_dict(self):
        """Test conversion to dictionary."""
        metadata = TemplateMetadata(
            name="test",
            description="Test description",
            category="professional",
            author="author",
            tags=["tag1", "tag2"],
        )

        result = metadata.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["description"] == "Test description"
        assert result["category"] == "professional"
        assert result["author"] == "author"
        assert result["tags"] == ["tag1", "tag2"]

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "name": "test_template",
            "description": "Test",
            "category": "modern",
            "author": "test_author",
            "version": "1.5.0",
            "tags": ["test"],
            "formats": ["md", "pdf"],
            "rating": 3.5,
            "reviews_count": 5,
            "downloads": 50,
        }

        metadata = TemplateMetadata.from_dict(data)

        assert metadata.name == "test_template"
        assert metadata.category == "modern"
        assert metadata.author == "test_author"
        assert metadata.version == "1.5.0"
        assert metadata.rating == 3.5

    def test_from_dict_missing_fields(self):
        """Test creation from dictionary with missing fields."""
        data = {"name": "test", "description": "Test", "category": "professional"}

        metadata = TemplateMetadata.from_dict(data)

        assert metadata.name == "test"
        assert metadata.author == "unknown"
        assert metadata.version == "1.0.0"
        assert metadata.tags == []


class TestTemplateMarketplaceInitialization:
    """Test TemplateMarketplace initialization."""

    def test_init_default_paths(self, temp_dir: Path):
        """Test initialization with default paths."""
        registry_path = temp_dir / "registry.json"
        user_templates_dir = temp_dir / "user_templates"

        _marketplace = TemplateMarketplace(
            registry_path=registry_path, user_templates_dir=user_templates_dir
        )

        assert _marketplace.registry_path == registry_path
        assert _marketplace.user_templates_dir == user_templates_dir
        # Registry file is created when saved (not on init)
        assert user_templates_dir.exists()

    def test_init_creates_directories(self, temp_dir: Path):
        """Test initialization creates necessary directories."""
        registry_path = temp_dir / "nested" / "registry.json"
        user_templates_dir = temp_dir / "nested" / "templates"

        _marketplace = TemplateMarketplace(
            registry_path=registry_path, user_templates_dir=user_templates_dir
        )

        assert registry_path.parent.exists()
        assert user_templates_dir.exists()

    def test_init_loads_default_registry(self, temp_dir: Path):
        """Test initialization loads default registry."""
        registry_path = temp_dir / "registry.json"
        _marketplace = TemplateMarketplace(registry_path=registry_path)

        assert "templates" in _marketplace.registry
        assert "categories" in _marketplace.registry
        assert "metadata" in _marketplace.registry

    def test_init_with_existing_registry(self, temp_dir: Path):
        """Test initialization loads existing registry."""
        registry_path = temp_dir / "registry.json"
        registry_data = {"templates": {"custom": {"name": "custom"}}, "categories": []}

        with open(registry_path, "w") as f:
            json.dump(registry_data, f)

        _marketplace = TemplateMarketplace(registry_path=registry_path)

        assert "custom" in _marketplace.registry["templates"]


class TestTemplateMarketplaceListTemplates:
    """Test list_templates method."""

    def test_list_all_templates(self, temp_dir: Path):
        """Test listing all templates."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        templates = _marketplace.list_templates()

        assert isinstance(templates, list)
        assert len(templates) > 0
        assert all(isinstance(t, TemplateMetadata) for t in templates)

    def test_list_templates_by_category(self, temp_dir: Path):
        """Test filtering templates by category."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        templates = _marketplace.list_templates(category="professional")

        assert all(t.category == "professional" for t in templates)

    def test_list_templates_by_tag(self, temp_dir: Path):
        """Test filtering templates by tag."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        templates = _marketplace.list_templates(tag="markdown")

        assert all("markdown" in t.tags for t in templates)

    def test_list_templates_sorted_by_rating(self, temp_dir: Path):
        """Test templates are sorted by rating."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        # Add templates with different ratings
        _marketplace.registry["templates"]["high_rated"] = TemplateMetadata(
            name="high_rated", description="High", category="professional", rating=5.0, downloads=10
        ).to_dict()
        _marketplace.registry["templates"]["low_rated"] = TemplateMetadata(
            name="low_rated", description="Low", category="professional", rating=1.0, downloads=100
        ).to_dict()
        _marketplace._save_registry()

        templates = _marketplace.list_templates()

        # Higher rated should come first
        ratings = [t.rating for t in templates]
        assert ratings == sorted(ratings, reverse=True)


class TestTemplateMarketplaceCategories:
    """Test category-related methods."""

    def test_get_categories(self, temp_dir: Path):
        """Test getting available categories."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        categories = _marketplace.get_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "professional" in categories
        assert "modern" in categories


class TestTemplateMarketplaceGetTemplate:
    """Test get_template method."""

    def test_get_existing_template(self, temp_dir: Path):
        """Test getting an existing template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        template = _marketplace.get_template("resume_md")

        assert template is not None
        assert template.name == "resume_md"

    def test_get_nonexistent_template(self, temp_dir: Path):
        """Test getting a non-existent template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        template = _marketplace.get_template("nonexistent")

        assert template is None


class TestTemplateMarketplacePreview:
    """Test preview_template method."""

    def test_preview_existing_template(self, temp_dir: Path):
        """Test previewing an existing template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        preview = _marketplace.preview_template("resume_md", lines=10)

        assert preview is not None
        assert isinstance(preview, str)
        assert len(preview.split("\n")) <= 10

    def test_preview_nonexistent_template(self, temp_dir: Path):
        """Test previewing a non-existent template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        preview = _marketplace.preview_template("nonexistent")

        assert preview is None


class TestTemplateMarketplaceInstall:
    """Test install_template method."""

    def test_install_template(self, temp_dir: Path):
        """Test installing a template from file."""
        _marketplace = TemplateMarketplace(
            registry_path=temp_dir / "registry.json",
            user_templates_dir=temp_dir / "user_templates",
        )

        # Create a test template file
        template_file = temp_dir / "test_template.j2"
        template_file.write_text("{# Test Template #}\nTest content")

        _installed_path = _marketplace.install_template(template_file)

        assert _installed_path.exists()
        assert _installed_path.name == "test_template.j2"
        assert "test_template" in _marketplace.registry["templates"]

    def test_install_template_with_custom_name(self, temp_dir: Path):
        """Test installing a template with custom name."""
        _marketplace = TemplateMarketplace(
            registry_path=temp_dir / "registry.json",
            user_templates_dir=temp_dir / "user_templates",
        )

        template_file = temp_dir / "test.j2"
        template_file.write_text("Test content")

        _installed_path = _marketplace.install_template(template_file, name="custom_name")

        assert "custom_name" in _marketplace.registry["templates"]
        assert _marketplace.registry["templates"]["custom_name"]["name"] == "custom_name"

    def test_install_template_with_metadata(self, temp_dir: Path):
        """Test installing a template with custom metadata."""
        _marketplace = TemplateMarketplace(
            registry_path=temp_dir / "registry.json",
            user_templates_dir=temp_dir / "user_templates",
        )

        template_file = temp_dir / "test.j2"
        template_file.write_text("Test content")

        metadata = TemplateMetadata(
            name="test",
            description="Custom description",
            category="modern",
            author="test_author",
        )

        _marketplace.install_template(template_file, metadata=metadata)

        stored = _marketplace.get_template("test")
        assert stored.description == "Custom description"
        assert stored.category == "modern"
        assert stored.author == "test_author"

    def test_install_template_file_not_found(self, temp_dir: Path):
        """Test installing a non-existent template file."""
        _marketplace = TemplateMarketplace(
            registry_path=temp_dir / "registry.json",
            user_templates_dir=temp_dir / "user_templates",
        )

        with pytest.raises(FileNotFoundError):
            _marketplace.install_template(temp_dir / "nonexistent.j2")

    def test_install_template_wrong_extension(self, temp_dir: Path):
        """Test installing a template with wrong extension."""
        _marketplace = TemplateMarketplace(
            registry_path=temp_dir / "registry.json",
            user_templates_dir=temp_dir / "user_templates",
        )

        template_file = temp_dir / "test.txt"
        template_file.write_text("Test content")

        with pytest.raises(ValueError, match=r"\.j2 extension"):
            _marketplace.install_template(template_file)


class TestTemplateMarketplaceUninstall:
    """Test uninstall_template method."""

    def test_uninstall_user_template(self, temp_dir: Path):
        """Test uninstalling a user template."""
        _marketplace = TemplateMarketplace(
            registry_path=temp_dir / "registry.json",
            user_templates_dir=temp_dir / "user_templates",
        )

        # Install a template first
        template_file = temp_dir / "test.j2"
        template_file.write_text("Test content")
        _marketplace.install_template(template_file)

        # Uninstall it
        result = _marketplace.uninstall_template("test")

        assert result is True
        assert "test" not in _marketplace.registry["templates"]

    def test_uninstall_builtin_template_raises(self, temp_dir: Path):
        """Test uninstalling a builtin template raises error."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        with pytest.raises(ValueError, match="builtin"):
            _marketplace.uninstall_template("resume_md")

    def test_uninstall_nonexistent_template(self, temp_dir: Path):
        """Test uninstalling a non-existent template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        result = _marketplace.uninstall_template("nonexistent")

        assert result is False


class TestTemplateMarketplaceRating:
    """Test rating-related methods."""

    def test_rate_template(self, temp_dir: Path):
        """Test rating a template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        result = _marketplace.rate_template("resume_md", rating=4.0)

        assert result is True
        template = _marketplace.get_template("resume_md")
        assert template.rating > 0
        assert template.reviews_count == 1

    def test_rate_template_invalid_rating(self, temp_dir: Path):
        """Test rating with invalid value."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        with pytest.raises(ValueError, match="between 1.0 and 5.0"):
            _marketplace.rate_template("resume_md", rating=6.0)

        with pytest.raises(ValueError, match="between 1.0 and 5.0"):
            _marketplace.rate_template("resume_md", rating=0.0)

    def test_rate_template_nonexistent(self, temp_dir: Path):
        """Test rating a non-existent template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        result = _marketplace.rate_template("nonexistent", rating=4.0)

        assert result is False

    def test_rate_template_with_review(self, temp_dir: Path):
        """Test rating with a review."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        _marketplace.rate_template("resume_md", rating=5.0, review="Great template!")

        reviews = _marketplace.get_reviews("resume_md")
        assert len(reviews) == 1
        assert reviews[0]["review"] == "Great template!"
        assert reviews[0]["rating"] == 5.0

    def test_multiple_ratings_average(self, temp_dir: Path):
        """Test multiple ratings are averaged."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        _marketplace.rate_template("resume_md", rating=3.0)
        _marketplace.rate_template("resume_md", rating=5.0)

        template = _marketplace.get_template("resume_md")
        assert template.rating == 4.0
        assert template.reviews_count == 2


class TestTemplateMarketplaceReviews:
    """Test review-related methods."""

    def test_get_reviews_empty(self, temp_dir: Path):
        """Test getting reviews for template with no reviews."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        reviews = _marketplace.get_reviews("resume_md")

        assert reviews == []

    def test_get_reviews_nonexistent_template(self, temp_dir: Path):
        """Test getting reviews for non-existent template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        reviews = _marketplace.get_reviews("nonexistent")

        assert reviews == []


class TestTemplateMarketplaceExport:
    """Test export_template method."""

    def test_export_builtin_template(self, temp_dir: Path):
        """Test exporting a builtin template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        output_path = temp_dir / "exported.j2"
        exported = _marketplace.export_template("resume_md", output_path)

        assert exported.exists()
        assert exported == output_path

    def test_export_increments_downloads(self, temp_dir: Path):
        """Test exporting increments download count."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        initial_downloads = _marketplace.get_template("resume_md").downloads

        _marketplace.export_template("resume_md", temp_dir / "exported.j2")

        template = _marketplace.get_template("resume_md")
        assert template.downloads == initial_downloads + 1

    def test_export_nonexistent_template(self, temp_dir: Path):
        """Test exporting a non-existent template."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        with pytest.raises(ValueError, match="not found"):
            _marketplace.export_template("nonexistent", temp_dir / "exported.j2")


class TestTemplateMarketplaceSearch:
    """Test search_templates method."""

    def test_search_by_name(self, temp_dir: Path):
        """Test searching templates by name."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        results = _marketplace.search_templates("resume_md")

        assert len(results) > 0
        assert any("resume_md" in t.name for t in results)

    def test_search_by_description(self, temp_dir: Path):
        """Test searching templates by description."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        results = _marketplace.search_templates("Markdown")

        assert len(results) > 0

    def test_search_by_tag(self, temp_dir: Path):
        """Test searching templates by tag."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        results = _marketplace.search_templates("modern")

        assert len(results) > 0

    def test_search_no_results(self, temp_dir: Path):
        """Test searching with no results."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        results = _marketplace.search_templates("xyznonexistent123")

        assert results == []


class TestTemplateMarketplaceRegistryPersistence:
    """Test registry persistence."""

    def test_registry_saved_after_install(self, temp_dir: Path):
        """Test registry is saved after installing template."""
        registry_path = temp_dir / "registry.json"
        _marketplace = TemplateMarketplace(
            registry_path=registry_path,
            user_templates_dir=temp_dir / "user_templates",
        )

        # Install a template
        template_file = temp_dir / "test.j2"
        template_file.write_text("Test")
        _marketplace.install_template(template_file)

        # Create new marketplace instance
        marketplace2 = TemplateMarketplace(registry_path=registry_path)

        assert "test" in marketplace2.registry["templates"]

    def test_registry_saved_after_rating(self, temp_dir: Path):
        """Test registry is saved after rating template."""
        registry_path = temp_dir / "registry.json"
        _marketplace = TemplateMarketplace(registry_path=registry_path)

        _marketplace.rate_template("resume_md", rating=4.0)

        # Create new marketplace instance
        marketplace2 = TemplateMarketplace(registry_path=registry_path)

        template = marketplace2.get_template("resume_md")
        assert template.reviews_count == 1


class TestTemplateMetadataValidation:
    """Test template metadata validation."""

    def test_rating_bounds(self, temp_dir: Path):
        """Test rating is within bounds."""
        _marketplace = TemplateMarketplace(registry_path=temp_dir / "registry.json")

        # Test minimum bound
        with pytest.raises(ValueError):
            _marketplace.rate_template("resume_md", rating=0.0)

        # Test maximum bound
        with pytest.raises(ValueError):
            _marketplace.rate_template("resume_md", rating=6.0)

        # Test valid bounds
        assert _marketplace.rate_template("resume_md", rating=1.0)
        assert _marketplace.rate_template("resume_md", rating=5.0)
