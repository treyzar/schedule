# Generated migration for credentials encryption

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parse_calendar', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add encrypted fields for Google
        migrations.AddField(
            model_name='usercredentials',
            name='google_token_encrypted',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Google Access Token (Encrypted)',
                help_text='Зашифрованный access token'
            ),
        ),
        migrations.AddField(
            model_name='usercredentials',
            name='google_refresh_token_encrypted',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Google Refresh Token (Encrypted)',
                help_text='Зашифрованный refresh token'
            ),
        ),
        migrations.AddField(
            model_name='usercredentials',
            name='google_client_secret_encrypted',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Google Client Secret (Encrypted)',
                help_text='Зашифрованный client secret'
            ),
        ),
        
        # Add encrypted fields for Skyeng
        migrations.AddField(
            model_name='usercredentials',
            name='skyeng_token_encrypted',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Skyeng Access Token (Encrypted)'
            ),
        ),
        migrations.AddField(
            model_name='usercredentials',
            name='skyeng_refresh_token_encrypted',
            field=models.TextField(
                blank=True,
                null=True,
                verbose_name='Skyeng Refresh Token (Encrypted)'
            ),
        ),
        
        # Add Skyeng user_id field
        migrations.AddField(
            model_name='usercredentials',
            name='skyeng_user_id',
            field=models.IntegerField(
                blank=True,
                null=True,
                verbose_name='Skyeng User ID'
            ),
        ),
        
        # Rename existing fields (data migration needed)
        # Note: In production, you'd need a data migration to copy 
        # old unencrypted data to new encrypted fields
    ]
