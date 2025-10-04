from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Shipment, StatusUpdate, ShipmentStatus

# Helper to sync Shipment.current_status based on latest StatusUpdate
def _sync_shipment_current_status(shipment: Shipment):
    latest = shipment.status_updates.order_by("-timestamp", "-id").first()
    new_status = latest.status if latest else ShipmentStatus.NEW  
    if shipment.current_status != new_status:
        Shipment.objects.filter(pk=shipment.pk).update(
            current_status=new_status,
            updated_at=timezone.now(),
        )

# Signal handlers to keep Shipment.current_status in sync
@receiver(post_save, sender=StatusUpdate)
def statusupdate_saved(sender, instance: StatusUpdate, **kwargs):
    _sync_shipment_current_status(instance.shipment)

# Also handle deletions of StatusUpdate
@receiver(post_delete, sender=StatusUpdate)
def statusupdate_deleted(sender, instance: StatusUpdate, **kwargs):
    _sync_shipment_current_status(instance.shipment)
