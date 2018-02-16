# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=80)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    name = models.CharField(max_length=50)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField()
    is_superuser = models.IntegerField()
    username = models.CharField(unique=True, max_length=30)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.CharField(max_length=75)
    is_staff = models.IntegerField()
    is_active = models.IntegerField()
    date_joined = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class CeleryTaskmeta(models.Model):
    task_id = models.CharField(unique=True, max_length=255)
    status = models.CharField(max_length=50)
    result = models.TextField(blank=True, null=True)
    date_done = models.DateTimeField()
    traceback = models.TextField(blank=True, null=True)
    hidden = models.IntegerField()
    meta = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'celery_taskmeta'


class CeleryTasksetmeta(models.Model):
    taskset_id = models.CharField(unique=True, max_length=255)
    result = models.TextField()
    date_done = models.DateTimeField()
    hidden = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'celery_tasksetmeta'


class DjangoAdminLog(models.Model):
    action_time = models.DateTimeField()
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    name = models.CharField(max_length=100)
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoEvolution(models.Model):
    version_id = models.IntegerField()
    app_label = models.CharField(max_length=200)
    label = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_evolution'


class DjangoProjectVersion(models.Model):
    signature = models.TextField()
    when = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_project_version'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class DjceleryCrontabschedule(models.Model):
    minute = models.CharField(max_length=64)
    hour = models.CharField(max_length=64)
    day_of_week = models.CharField(max_length=64)
    day_of_month = models.CharField(max_length=64)
    month_of_year = models.CharField(max_length=64)

    class Meta:
        managed = False
        db_table = 'djcelery_crontabschedule'


class DjceleryIntervalschedule(models.Model):
    every = models.IntegerField()
    period = models.CharField(max_length=24)

    class Meta:
        managed = False
        db_table = 'djcelery_intervalschedule'


class DjceleryPeriodictask(models.Model):
    name = models.CharField(unique=True, max_length=200)
    task = models.CharField(max_length=200)
    interval = models.ForeignKey(DjceleryIntervalschedule, models.DO_NOTHING, blank=True, null=True)
    crontab = models.ForeignKey(DjceleryCrontabschedule, models.DO_NOTHING, blank=True, null=True)
    args = models.TextField()
    kwargs = models.TextField()
    queue = models.CharField(max_length=200, blank=True, null=True)
    exchange = models.CharField(max_length=200, blank=True, null=True)
    routing_key = models.CharField(max_length=200, blank=True, null=True)
    expires = models.DateTimeField(blank=True, null=True)
    enabled = models.IntegerField()
    last_run_at = models.DateTimeField(blank=True, null=True)
    total_run_count = models.PositiveIntegerField()
    date_changed = models.DateTimeField()
    description = models.TextField()

    class Meta:
        managed = False
        db_table = 'djcelery_periodictask'


class DjceleryPeriodictasks(models.Model):
    ident = models.SmallIntegerField(primary_key=True)
    last_update = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'djcelery_periodictasks'


class DjceleryTaskstate(models.Model):
    state = models.CharField(max_length=64)
    task_id = models.CharField(unique=True, max_length=36)
    name = models.CharField(max_length=200, blank=True, null=True)
    tstamp = models.DateTimeField()
    args = models.TextField(blank=True, null=True)
    kwargs = models.TextField(blank=True, null=True)
    eta = models.DateTimeField(blank=True, null=True)
    expires = models.DateTimeField(blank=True, null=True)
    result = models.TextField(blank=True, null=True)
    traceback = models.TextField(blank=True, null=True)
    runtime = models.FloatField(blank=True, null=True)
    retries = models.IntegerField()
    worker = models.ForeignKey('DjceleryWorkerstate', models.DO_NOTHING, blank=True, null=True)
    hidden = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'djcelery_taskstate'


class DjceleryWorkerstate(models.Model):
    hostname = models.CharField(unique=True, max_length=255)
    last_heartbeat = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'djcelery_workerstate'


class MaqluengineAjaxrequestdata(models.Model):
    uuid = models.CharField(max_length=32)
    is_finished = models.IntegerField()
    jsonstring = models.TextField(db_column='jsonString')  # Field name made lowercase.
    keep_alive = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_ajaxrequestdata'


class MaqluengineForm(models.Model):
    form_type_id = models.IntegerField()
    form_geojson_string = models.TextField(blank=True, null=True)
    form_number = models.IntegerField(blank=True, null=True)
    form_name = models.CharField(max_length=50, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    is_public = models.IntegerField()
    hierarchy_parent_id = models.IntegerField(blank=True, null=True)
    project_id = models.IntegerField()
    sort_index = models.CharField(unique=True, max_length=255)
    flagged_for_deletion = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_form'


class MaqluengineFormproject(models.Model):
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    is_public = models.IntegerField()
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    uri_img = models.CharField(max_length=255, blank=True, null=True)
    uri_thumbnail = models.CharField(max_length=255, blank=True, null=True)
    uri_download = models.CharField(max_length=255, blank=True, null=True)
    uri_upload = models.CharField(max_length=255, blank=True, null=True)
    uri_upload_key = models.CharField(max_length=255, blank=True, null=True)
    geojson_string = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maqluengine_formproject'


class MaqluengineFormrecordattributetype(models.Model):
    record_type = models.CharField(max_length=50, blank=True, null=True)
    form_type_id = models.IntegerField()
    order_number = models.IntegerField(blank=True, null=True)
    is_public = models.IntegerField()
    project_id = models.IntegerField()
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    flagged_for_deletion = models.IntegerField()
    is_numeric = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_formrecordattributetype'


class MaqluengineFormrecordattributevalue(models.Model):
    record_value = models.TextField(blank=True, null=True)
    record_attribute_type_id = models.IntegerField()
    form_parent_id = models.IntegerField(blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    project_id = models.IntegerField()
    flagged_for_deletion = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_formrecordattributevalue'


class MaqluengineFormrecordreferencetype(models.Model):
    record_type = models.CharField(max_length=50, blank=True, null=True)
    form_type_parent_id = models.IntegerField(blank=True, null=True)
    form_type_reference_id = models.IntegerField(blank=True, null=True)
    order_number = models.IntegerField(blank=True, null=True)
    is_public = models.IntegerField()
    project_id = models.IntegerField()
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    flagged_for_deletion = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_formrecordreferencetype'


class MaqluengineFormrecordreferencevalue(models.Model):
    form_parent_id = models.IntegerField()
    record_reference_type_id = models.IntegerField()
    external_key_reference = models.CharField(max_length=250, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    project_id = models.IntegerField()
    flagged_for_deletion = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_formrecordreferencevalue'


class MaqluengineFormrecordreferencevalueRecordReference(models.Model):
    formrecordreferencevalue_id = models.IntegerField()
    form_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_formrecordreferencevalue_record_reference'
        unique_together = (('formrecordreferencevalue_id', 'form_id'),)


class MaqluengineFormtype(models.Model):
    form_type_name = models.CharField(max_length=50, blank=True, null=True)
    project_id = models.IntegerField()
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    is_public = models.IntegerField()
    form_type_group_id = models.IntegerField(blank=True, null=True)
    type = models.IntegerField()
    media_type = models.IntegerField()
    is_hierarchical = models.IntegerField()
    file_extension = models.CharField(max_length=10, blank=True, null=True)
    uri_prefix = models.CharField(max_length=20, blank=True, null=True)
    template_json = models.TextField(blank=True, null=True)
    flagged_for_deletion = models.IntegerField()
    is_numeric = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_formtype'


class MaqluengineFormtypegroup(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    date_created = models.DateTimeField(blank=True, null=True)
    created_by_id = models.IntegerField(blank=True, null=True)
    date_last_modified = models.DateTimeField(blank=True, null=True)
    modified_by_id = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    project_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'maqluengine_formtypegroup'


class MaqluenginePermissions(models.Model):
    user_id = models.IntegerField(unique=True)
    project_id = models.IntegerField(blank=True, null=True)
    access_level = models.IntegerField(blank=True, null=True)
    job_title = models.CharField(max_length=100)
    custom_templates = models.TextField(blank=True, null=True)
    saved_queries = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'maqluengine_permissions'


class SouthMigrationhistory(models.Model):
    app_name = models.CharField(max_length=255)
    migration = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'south_migrationhistory'
