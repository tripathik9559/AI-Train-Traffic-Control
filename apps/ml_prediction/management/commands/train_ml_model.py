"""Management command to train the ML delay prediction model."""
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Train the Random Forest delay prediction model'

    def handle(self, *args, **options):
        from apps.ml_prediction.ml.trainer import DelayModelTrainer

        self.stdout.write(self.style.MIGRATE_HEADING('Training ML Delay Prediction Model...'))
        trainer = DelayModelTrainer(model_dir=str(settings.ML_MODELS_DIR))
        metrics = trainer.train()

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Model trained successfully!\n'
            f'   R² Score:      {metrics["r2_score"]}\n'
            f'   MAE:           {metrics["mean_absolute_error"]} minutes\n'
            f'   RMSE:          {metrics["root_mean_squared_error"]} minutes\n'
            f'   Cross-Val R²:  {metrics["cross_val_score"]}\n'
            f'   Samples:       {metrics["training_samples"]}\n'
            f'   Model saved:   {metrics["model_path"]}\n'
        ))
