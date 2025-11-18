import { useState, useEffect } from 'react';
import { ProductionCard } from './ProductionCard';
import { Clock } from 'lucide-react';

export interface ProductionOrder {
  id: string;
  productName: string;
  quantity: number;
  deadline: Date;
}

// Mock data - replace with real data source
const INITIAL_ORDERS: ProductionOrder[] = [
  {
    id: '1',
    productName: 'Chocolate Croissants',
    quantity: 48,
    deadline: new Date(Date.now() + 15 * 60 * 1000), // 15 minutes
  },
  {
    id: '2',
    productName: 'Baguettes',
    quantity: 120,
    deadline: new Date(Date.now() + 45 * 60 * 1000), // 45 minutes
  },
  {
    id: '3',
    productName: 'Sourdough Loaves',
    quantity: 36,
    deadline: new Date(Date.now() + 90 * 60 * 1000), // 90 minutes
  },
  {
    id: '4',
    productName: 'Fruit Tarts',
    quantity: 24,
    deadline: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes late
  },
  {
    id: '5',
    productName: 'Pain au Chocolat',
    quantity: 60,
    deadline: new Date(Date.now() + 120 * 60 * 1000), // 2 hours
  },
  {
    id: '6',
    productName: 'Brioche Buns',
    quantity: 72,
    deadline: new Date(Date.now() + 30 * 60 * 1000), // 30 minutes
  },
];

export function ProductionDashboard() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [orders] = useState<ProductionOrder[]>(INITIAL_ORDERS);

  // Update current time every second
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Calculate grid layout based on number of orders
  const getGridConfig = (orderCount: number) => {
    if (orderCount <= 3) return { cols: 3, size: 'large' };
    if (orderCount <= 6) return { cols: 3, size: 'medium' };
    if (orderCount <= 9) return { cols: 3, size: 'small' };
    if (orderCount <= 12) return { cols: 4, size: 'small' };
    if (orderCount <= 15) return { cols: 5, size: 'compact' };
    return { cols: 6, size: 'compact' };
  };

  const gridConfig = getGridConfig(orders.length);

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6 flex flex-col">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-5xl text-white mb-1">Production Dashboard</h1>
          <p className="text-2xl text-slate-300">Active Orders: {orders.length}</p>
        </div>
        <div className="flex items-center gap-3 text-white">
          <Clock className="w-10 h-10" />
          <div className="text-right">
            <div className="text-4xl">
              {currentTime.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: false 
              })}
            </div>
            <div className="text-xl text-slate-300">
              {currentTime.toLocaleDateString('en-US', { 
                weekday: 'long',
                month: 'short',
                day: 'numeric'
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Production Grid */}
      <div 
        className="grid gap-4 flex-1 overflow-hidden"
        style={{ 
          gridTemplateColumns: `repeat(${gridConfig.cols}, minmax(0, 1fr))`,
          gridAutoRows: '1fr'
        }}
      >
        {orders.map((order) => (
          <ProductionCard 
            key={order.id} 
            order={order} 
            currentTime={currentTime}
            size={gridConfig.size}
          />
        ))}
      </div>
    </div>
  );
}
