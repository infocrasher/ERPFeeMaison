import { ProductionOrder } from './ProductionDashboard';
import { Clock, Package, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface ProductionCardProps {
  order: ProductionOrder;
  currentTime: Date;
  size: 'large' | 'medium' | 'small' | 'compact';
}

type UrgencyLevel = 'late' | 'critical' | 'warning' | 'normal';

interface UrgencyConfig {
  bgColor: string;
  borderColor: string;
  textColor: string;
  iconColor: string;
  icon: React.ReactNode;
  label: string;
  glowColor: string;
}

function getUrgencyLevel(timeRemaining: number): UrgencyLevel {
  if (timeRemaining < 0) return 'late';
  if (timeRemaining < 20 * 60 * 1000) return 'critical'; // Less than 20 minutes
  if (timeRemaining < 45 * 60 * 1000) return 'warning'; // Less than 45 minutes
  return 'normal';
}

function formatTimeRemaining(milliseconds: number): string {
  const isNegative = milliseconds < 0;
  const absMs = Math.abs(milliseconds);
  
  const hours = Math.floor(absMs / (1000 * 60 * 60));
  const minutes = Math.floor((absMs % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((absMs % (1000 * 60)) / 1000);

  if (hours > 0) {
    return `${isNegative ? '-' : ''}${hours}h ${minutes}m`;
  }
  return `${isNegative ? '-' : ''}${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export function ProductionCard({ order, currentTime, size }: ProductionCardProps) {
  const timeRemaining = order.deadline.getTime() - currentTime.getTime();
  const urgency = getUrgencyLevel(timeRemaining);

  // Size configurations
  const sizeConfigs = {
    large: {
      iconSize: 'w-16 h-16',
      statusIcon: 'w-14 h-14',
      labelText: 'text-3xl',
      titleText: 'text-5xl',
      quantityLabel: 'text-2xl',
      quantityValue: 'text-6xl',
      timeLabel: 'text-2xl',
      timeValue: 'text-7xl',
      deadlineText: 'text-2xl',
      padding: 'p-6',
      gap: 'gap-4',
      mb: 'mb-6'
    },
    medium: {
      iconSize: 'w-12 h-12',
      statusIcon: 'w-10 h-10',
      labelText: 'text-2xl',
      titleText: 'text-4xl',
      quantityLabel: 'text-xl',
      quantityValue: 'text-5xl',
      timeLabel: 'text-xl',
      timeValue: 'text-6xl',
      deadlineText: 'text-xl',
      padding: 'p-4',
      gap: 'gap-3',
      mb: 'mb-4'
    },
    small: {
      iconSize: 'w-8 h-8',
      statusIcon: 'w-8 h-8',
      labelText: 'text-xl',
      titleText: 'text-3xl',
      quantityLabel: 'text-lg',
      quantityValue: 'text-4xl',
      timeLabel: 'text-lg',
      timeValue: 'text-5xl',
      deadlineText: 'text-lg',
      padding: 'p-4',
      gap: 'gap-2',
      mb: 'mb-3'
    },
    compact: {
      iconSize: 'w-6 h-6',
      statusIcon: 'w-6 h-6',
      labelText: 'text-lg',
      titleText: 'text-2xl',
      quantityLabel: 'text-base',
      quantityValue: 'text-3xl',
      timeLabel: 'text-base',
      timeValue: 'text-4xl',
      deadlineText: 'text-base',
      padding: 'p-3',
      gap: 'gap-2',
      mb: 'mb-2'
    }
  };

  const sizeConfig = sizeConfigs[size];

  const urgencyConfigs: Record<UrgencyLevel, UrgencyConfig> = {
    late: {
      bgColor: 'bg-red-950/50',
      borderColor: 'border-red-500',
      textColor: 'text-red-100',
      iconColor: 'text-red-400',
      icon: <XCircle className={sizeConfig.statusIcon} />,
      label: 'OVERDUE',
      glowColor: 'shadow-red-500/50',
    },
    critical: {
      bgColor: 'bg-orange-950/50',
      borderColor: 'border-orange-500',
      textColor: 'text-orange-100',
      iconColor: 'text-orange-400',
      icon: <AlertTriangle className={sizeConfig.statusIcon} />,
      label: 'URGENT',
      glowColor: 'shadow-orange-500/50',
    },
    warning: {
      bgColor: 'bg-yellow-950/50',
      borderColor: 'border-yellow-500',
      textColor: 'text-yellow-100',
      iconColor: 'text-yellow-400',
      icon: <Clock className={sizeConfig.statusIcon} />,
      label: 'SOON',
      glowColor: 'shadow-yellow-500/50',
    },
    normal: {
      bgColor: 'bg-green-950/50',
      borderColor: 'border-green-500',
      textColor: 'text-green-100',
      iconColor: 'text-green-400',
      icon: <CheckCircle className={sizeConfig.statusIcon} />,
      label: 'ON TIME',
      glowColor: 'shadow-green-500/50',
    },
  };

  const config = urgencyConfigs[urgency];

  return (
    <div 
      className={`
        ${config.bgColor} ${config.borderColor} ${config.textColor}
        border-4 rounded-2xl ${sizeConfig.padding}
        shadow-2xl ${config.glowColor}
        transform transition-all duration-300
        ${urgency === 'late' || urgency === 'critical' ? 'animate-pulse' : ''}
        flex flex-col h-full
      `}
    >
      {/* Status Badge */}
      <div className={`flex items-center justify-between ${sizeConfig.mb}`}>
        <div className={`${config.iconColor} flex items-center ${sizeConfig.gap}`}>
          {config.icon}
          <span className={sizeConfig.labelText}>{config.label}</span>
        </div>
      </div>

      {/* Product Name */}
      <h2 className={`${sizeConfig.titleText} ${sizeConfig.mb} leading-tight`}>
        {order.productName}
      </h2>

      {/* Quantity */}
      <div className={`flex items-center ${sizeConfig.gap} ${sizeConfig.mb}`}>
        <Package className={`${sizeConfig.iconSize} ${config.iconColor}`} />
        <div>
          <div className={`${sizeConfig.quantityLabel} text-slate-400`}>Quantité</div>
          <div className={sizeConfig.quantityValue}>{order.quantity}</div>
        </div>
      </div>

      {/* Time Remaining */}
      <div className={`mt-auto pt-4 border-t-2 border-current/20`}>
        <div className={`${sizeConfig.timeLabel} text-slate-400 mb-1`}>
          {timeRemaining < 0 ? 'En retard' : 'Temps restant'}
        </div>
        <div className={`${sizeConfig.timeValue} tracking-tight`}>
          {formatTimeRemaining(timeRemaining)}
        </div>
      </div>

      {/* Deadline */}
      <div className={`mt-2 ${sizeConfig.deadlineText} text-slate-400`}>
        Échéance: {order.deadline.toLocaleTimeString('fr-FR', { 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: false 
        })}
      </div>
    </div>
  );
}
