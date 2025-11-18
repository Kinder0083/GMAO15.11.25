import React from 'react';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "./alert-dialog";

export function ConfirmDialog({ 
  open, 
  onOpenChange, 
  title, 
  description, 
  onConfirm,
  confirmText = "Confirmer",
  cancelText = "Annuler",
  variant = "default" // "default" ou "destructive"
}) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription className="whitespace-pre-line">
            {description}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel onClick={() => onOpenChange(false)}>
            {cancelText}
          </AlertDialogCancel>
          <AlertDialogAction
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
            className={variant === "destructive" ? "bg-red-600 hover:bg-red-700" : ""}
          >
            {confirmText}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// Hook personnalisé pour faciliter l'utilisation
export function useConfirmDialog() {
  const [dialogState, setDialogState] = React.useState({
    open: false,
    title: '',
    description: '',
    onConfirm: () => {},
    confirmText: 'Confirmer',
    cancelText: 'Annuler',
    variant: 'default'
  });

  const confirm = ({
    title,
    description,
    onConfirm,
    confirmText = 'Confirmer',
    cancelText = 'Annuler',
    variant = 'default'
  }) => {
    setDialogState({
      open: true,
      title,
      description,
      onConfirm,
      confirmText,
      cancelText,
      variant
    });
  };

  const ConfirmDialogComponent = () => (
    <ConfirmDialog
      open={dialogState.open}
      onOpenChange={(open) => setDialogState(prev => ({ ...prev, open }))}
      title={dialogState.title}
      description={dialogState.description}
      onConfirm={dialogState.onConfirm}
      confirmText={dialogState.confirmText}
      cancelText={dialogState.cancelText}
      variant={dialogState.variant}
    />
  );

  return { confirm, ConfirmDialog: ConfirmDialogComponent };
}
