# Generated by Django 2.0.2 on 2018-02-16 17:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AJAXRequestData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(max_length=32)),
                ('is_finished', models.BooleanField(default=False)),
                ('keep_alive', models.BooleanField(default=True)),
                ('jsonString', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('form_name', models.CharField(blank=True, max_length=50, null=True)),
                ('form_number', models.IntegerField(blank=True, null=True)),
                ('form_geojson_string', models.TextField(blank=True, null=True)),
                ('is_public', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('sort_index', models.CharField(max_length=255, unique=True)),
                ('flagged_for_deletion', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='form_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FormProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, verbose_name='Project Name')),
                ('description', models.TextField(blank=True, null=True)),
                ('uri_img', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('uri_thumbnail', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('uri_download', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('uri_upload', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('uri_upload_key', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('geojson_string', models.TextField(blank=True, null=True)),
                ('is_public', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='project_ref_to_user_modifier', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FormRecordAttributeType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_type', models.CharField(blank=True, max_length=50, null=True)),
                ('order_number', models.IntegerField(blank=True, null=True)),
                ('is_numeric', models.BooleanField(default=False)),
                ('is_public', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('flagged_for_deletion', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='frat_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FormRecordAttributeValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_value', models.TextField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('flagged_for_deletion', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formatt_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
                ('form_parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='maqluengine.Form')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formatt_ref_to_user_modifier', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject')),
                ('record_attribute_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormRecordAttributeType')),
            ],
        ),
        migrations.CreateModel(
            name='FormRecordReferenceType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_type', models.CharField(blank=True, max_length=50, null=True)),
                ('order_number', models.IntegerField(blank=True, null=True)),
                ('is_public', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('flagged_for_deletion', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='frrt_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FormRecordReferenceValue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('external_key_reference', models.CharField(blank=True, max_length=250, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('flagged_for_deletion', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formref_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
                ('form_parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ref_to_parent_form', to='maqluengine.Form')),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formref_ref_to_user_modifier', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject')),
                ('record_reference', models.ManyToManyField(blank=True, null=True, related_name='ref_to_value_form', to='maqluengine.Form')),
                ('record_reference_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormRecordReferenceType')),
            ],
        ),
        migrations.CreateModel(
            name='FormType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('form_type_name', models.CharField(blank=True, max_length=50, null=True)),
                ('type', models.IntegerField()),
                ('media_type', models.IntegerField(default=-1)),
                ('file_extension', models.CharField(blank=True, default='', max_length=10, null=True)),
                ('uri_prefix', models.CharField(blank=True, default='', max_length=20, null=True)),
                ('is_hierarchical', models.BooleanField(default=False)),
                ('is_numeric', models.BooleanField(default=False)),
                ('template_json', models.TextField(blank=True, null=True)),
                ('is_public', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('flagged_for_deletion', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formtype_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='FormTypeGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=50, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True, null=True)),
                ('date_last_modified', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formtypegroup_ref_to_user_creator', to=settings.AUTH_USER_MODEL)),
                ('modified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formtypegroup_ref_to_user_modifier', to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject')),
            ],
        ),
        migrations.CreateModel(
            name='Permissions',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_level', models.IntegerField(blank=True, null=True)),
                ('job_title', models.CharField(max_length=100, verbose_name='Enter a Title')),
                ('custom_templates', models.TextField(blank=True, null=True)),
                ('saved_queries', models.TextField(blank=True, null=True)),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='formtype',
            name='form_type_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='maqluengine.FormTypeGroup'),
        ),
        migrations.AddField(
            model_name='formtype',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='formtype_ref_to_user_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='formtype',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject'),
        ),
        migrations.AddField(
            model_name='formrecordreferencetype',
            name='form_type_parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ref_to_parent_formtype', to='maqluengine.FormType'),
        ),
        migrations.AddField(
            model_name='formrecordreferencetype',
            name='form_type_reference',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ref_to_value_formtype', to='maqluengine.FormType'),
        ),
        migrations.AddField(
            model_name='formrecordreferencetype',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='frrt_ref_to_user_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='formrecordreferencetype',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject'),
        ),
        migrations.AddField(
            model_name='formrecordattributetype',
            name='form_type',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormType'),
        ),
        migrations.AddField(
            model_name='formrecordattributetype',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='frat_ref_to_user_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='formrecordattributetype',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject'),
        ),
        migrations.AddField(
            model_name='form',
            name='form_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormType'),
        ),
        migrations.AddField(
            model_name='form',
            name='hierarchy_parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='maqluengine.Form'),
        ),
        migrations.AddField(
            model_name='form',
            name='modified_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='form_ref_to_user_modifier', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='form',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='maqluengine.FormProject'),
        ),
    ]
