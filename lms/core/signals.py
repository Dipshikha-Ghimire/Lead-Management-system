from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User, Group
from .models import Staff


@receiver(post_save, sender=User)
def create_staff_on_group_add(sender, instance, created, **kwargs):
    if created:
        staff_group = Group.objects.filter(name='Staff').first()
        if staff_group and staff_group in instance.groups.all():
            try:
                staff = Staff.objects.get(user=instance)
            except Staff.DoesNotExist:
                Staff.objects.create(
                    user=instance,
                    full_name=instance.get_full_name() or instance.username,
                    email=instance.email,
                    role='staff'
                )


@receiver(post_delete, sender=Staff)
def delete_user_on_staff_delete(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()


def sync_staff_from_groups(user):
    staff_group = Group.objects.filter(name='Staff').first()
    if not staff_group:
        return
    
    is_in_staff_group = staff_group in user.groups.all()
    
    try:
        staff = Staff.objects.get(user=user)
        if not is_in_staff_group:
            pass
    except Staff.DoesNotExist:
        if is_in_staff_group:
            Staff.objects.create(
                user=user,
                full_name=user.get_full_name() or user.username,
                email=user.email,
                role='staff'
            )
