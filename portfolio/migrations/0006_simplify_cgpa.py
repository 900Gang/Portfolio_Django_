from django.db import migrations


def simplify_cgpa(apps, schema_editor):
    Education = apps.get_model("portfolio", "Education")
    old = "CGPA: 6.84/10.0 — no current backlogs."
    for entry in Education.objects.using(schema_editor.connection.alias).filter(
        institution="College of Engineering, Muttathara", description__contains=old
    ):
        lines = entry.description.splitlines(keepends=True)
        entry.description = "".join(
            "CGPA: 6.84" + line[len(old):] if line.rstrip("\r\n") == old else line
            for line in lines
        )
        entry.save(update_fields=["description"], using=schema_editor.connection.alias)


class Migration(migrations.Migration):
    dependencies = [("portfolio", "0005_correct_portfolio_details")]
    operations = [migrations.RunPython(simplify_cgpa, migrations.RunPython.noop)]
