from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dhl_api', '0007_serviceareacitymap'),
    ]

    operations = [
        migrations.CreateModel(
            name='CountryISO',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(help_text='Código ISO alpha-2', max_length=2, unique=True)),
                ('iso_short_name', models.CharField(blank=True, max_length=200)),
                ('iso_full_name', models.CharField(blank=True, max_length=255)),
                ('dhl_short_name', models.CharField(blank=True, max_length=200)),
                ('currency_code', models.CharField(blank=True, max_length=3)),
                ('numeric_code', models.CharField(blank=True, max_length=3)),
                ('alt_code', models.CharField(blank=True, help_text='ISO Alternate Code', max_length=3)),
                ('dial_in', models.CharField(blank=True, max_length=10)),
                ('dial_out', models.CharField(blank=True, max_length=10)),
                ('independent', models.CharField(blank=True, help_text='Y/N', max_length=1)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'País ISO',
                'verbose_name_plural': 'Países ISO',
            },
        ),
        migrations.AddIndex(
            model_name='countryiso',
            index=models.Index(fields=['code'], name='dhl_api_cou_code_idx'),
        ),
    ]
