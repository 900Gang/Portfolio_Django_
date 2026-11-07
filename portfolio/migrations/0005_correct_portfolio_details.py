from django.db import migrations


CERTIFICATIONS = (
    "Basic to Advanced SQL",
    "Basic to Advanced Power BI Certificate",
    "Basic to Advanced Tableau Dashboard",
    "Basic to Advanced Microsoft Excel",
    "Basic to Advanced PowerPoint",
)


def correct_details(apps, schema_editor):
    database = schema_editor.connection.alias
    Education = apps.get_model("portfolio", "Education")
    JourneyEntry = apps.get_model("portfolio", "JourneyEntry")
    Certification = apps.get_model("portfolio", "Certification")

    education_changes = (
        ("College of Engineering, Muttathara", "CGPA: 6.82/10.0", "CGPA: 6.84/10.0"),
        ("Sree Narayana Public School", "CGPA: 8.2", "Percentage: 82%"),
    )
    for institution, old, new in education_changes:
        for entry in Education.objects.using(database).filter(
            institution=institution, description__contains=old
        ):
            lines = entry.description.splitlines(keepends=True)
            entry.description = "".join(
                new + line[len(old):] if line.rstrip("\r\n") == old else
                line.replace(old, new) if old.endswith("/10.0") else line
                for line in lines
            )
            entry.save(update_fields=["description"], using=database)

    for entry in JourneyEntry.objects.using(database).filter(
        title="Graduated B.Tech in Computer Science Engineering",
        description__contains="CGPA of 6.82/10.0",
    ):
        entry.description = entry.description.replace("CGPA of 6.82/10.0", "CGPA of 6.84/10.0")
        entry.save(update_fields=["description"], using=database)

    for name in CERTIFICATIONS:
        records = Certification.objects.using(database).filter(name=name)
        if not records.filter(issuer="SkillNation").exists():
            records.filter(issuer="LinkedIn").update(issuer="SkillNation")


class Migration(migrations.Migration):
    dependencies = [("portfolio", "0004_chatlog")]
    operations = [migrations.RunPython(correct_details, migrations.RunPython.noop)]
