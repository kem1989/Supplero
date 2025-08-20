'use client';

import React, { useState } from 'react';
import { type SupplierCardData } from './SupplierCard';

export interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'warning' | 'danger';
  disabled?: boolean;
  loading?: boolean;
  tooltip?: string;
  confirmationRequired?: boolean;
  confirmationMessage?: string;
}

export interface QuickActionsProps {
  supplier: SupplierCardData;
  actions?: QuickAction[];
  layout?: 'horizontal' | 'vertical' | 'dropdown';
  size?: 'sm' | 'md' | 'lg';
  onAction?: (actionId: string, supplier: SupplierCardData) => void | Promise<void>;
  className?: string;
}

const VARIANT_CLASSES = {
  primary: 'bg-blue-600 hover:bg-blue-700 text-white border-blue-600',
  secondary: 'bg-slate-700 hover:bg-slate-600 text-slate-300 border-slate-600',
  warning: 'bg-yellow-600 hover:bg-yellow-700 text-white border-yellow-600',
  danger: 'bg-red-600 hover:bg-red-700 text-white border-red-600'
};

const SIZE_CLASSES = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base'
};

export default function QuickActions({
  supplier,
  actions,
  layout = 'horizontal',
  size = 'sm',
  onAction,
  className = ''
}: QuickActionsProps) {
  const [loadingAction, setLoadingAction] = useState<string | null>(null);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState<string | null>(null);

  // Default actions if none provided
  const defaultActions: QuickAction[] = [
    {
      id: 'view-details',
      label: 'View Details',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
      ),
      variant: 'secondary'
    },
    {
      id: 'analyze-risk',
      label: 'Analyze Risk',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
      variant: 'primary'
    },
    {
      id: 'toggle-watchlist',
      label: supplier.is_watchlisted ? 'Remove from Watchlist' : 'Add to Watchlist',
      icon: supplier.is_watchlisted ? (
        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
        </svg>
      ),
      variant: supplier.is_watchlisted ? 'warning' : 'secondary'
    },
    {
      id: 'view-contracts',
      label: 'View Contracts',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      variant: 'secondary',
      disabled: !supplier.contract_count || supplier.contract_count === 0
    },
    {
      id: 'edit-supplier',
      label: 'Edit',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      variant: 'secondary'
    },
    {
      id: 'generate-report',
      label: 'Generate Report',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
      variant: 'secondary'
    }
  ];

  const actionList = actions || defaultActions;
  const sizeClasses = SIZE_CLASSES[size];

  const handleActionClick = async (action: QuickAction) => {
    if (action.disabled || loadingAction === action.id) return;

    if (action.confirmationRequired) {
      setShowConfirmation(action.id);
      return;
    }

    await executeAction(action);
  };

  const executeAction = async (action: QuickAction) => {
    if (!onAction) return;

    try {
      setLoadingAction(action.id);
      await onAction(action.id, supplier);
    } catch (error) {
      console.error(`Action ${action.id} failed:`, error);
    } finally {
      setLoadingAction(null);
      setShowConfirmation(null);
    }
  };

  const renderActionButton = (action: QuickAction, isInDropdown = false) => {
    const isLoading = loadingAction === action.id;
    const baseClasses = `
      inline-flex items-center justify-center space-x-1 font-medium rounded border transition-all duration-200
      ${sizeClasses}
      ${isInDropdown ? 'w-full justify-start' : ''}
      ${action.disabled ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-sm'}
      ${VARIANT_CLASSES[action.variant || 'secondary']}
    `;

    return (
      <button
        key={action.id}
        onClick={() => handleActionClick(action)}
        disabled={action.disabled || isLoading}
        title={action.tooltip}
        className={baseClasses}
      >
        {isLoading ? (
          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        ) : (
          action.icon
        )}
        <span>{action.label}</span>
      </button>
    );
  };

  if (layout === 'dropdown') {
    return (
      <div className={`relative ${className}`}>
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className={`
            inline-flex items-center space-x-1 ${sizeClasses}
            ${VARIANT_CLASSES.secondary}
            rounded border font-medium transition-colors
          `}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
          </svg>
          <span>Actions</span>
        </button>

        {showDropdown && (
          <>
            <div 
              className="fixed inset-0 z-10" 
              onClick={() => setShowDropdown(false)}
            />
            <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-600 rounded-lg shadow-lg z-20">
              <div className="py-1">
                {actionList.map((action) => (
                  <div key={action.id} className="px-1">
                    {renderActionButton(action, true)}
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    );
  }

  const layoutClasses = layout === 'vertical' ? 'flex flex-col space-y-2' : 'flex space-x-2';

  return (
    <>
      <div className={`${layoutClasses} ${className}`}>
        {actionList.map((action) => renderActionButton(action))}
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-600 rounded-lg p-6 max-w-md mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">Confirm Action</h3>
            <p className="text-slate-300 mb-6">
              {actionList.find(a => a.id === showConfirmation)?.confirmationMessage || 
               'Are you sure you want to perform this action?'}
            </p>
            <div className="flex space-x-3 justify-end">
              <button
                onClick={() => setShowConfirmation(null)}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  const action = actionList.find(a => a.id === showConfirmation);
                  if (action) executeAction(action);
                }}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
              >
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// Pre-configured action sets for common use cases
export const createViewActions = (supplier: SupplierCardData): QuickAction[] => [
  {
    id: 'view-details',
    label: 'View Details',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
    variant: 'primary'
  },
  {
    id: 'view-contracts',
    label: 'Contracts',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    variant: 'secondary',
    disabled: !supplier.contract_count
  }
];

export const createAnalysisActions = (supplier: SupplierCardData): QuickAction[] => [
  {
    id: 'analyze-risk',
    label: 'Risk Analysis',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    variant: 'primary'
  },
  {
    id: 'generate-report',
    label: 'Generate Report',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
    variant: 'secondary'
  }
];

export const createManagementActions = (supplier: SupplierCardData): QuickAction[] => [
  {
    id: 'edit-supplier',
    label: 'Edit',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
    variant: 'secondary'
  },
  {
    id: 'toggle-watchlist',
    label: supplier.is_watchlisted ? 'Unwatch' : 'Watch',
    icon: supplier.is_watchlisted ? (
      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
      </svg>
    ) : (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    ),
    variant: supplier.is_watchlisted ? 'warning' : 'secondary'
  }
];
