/**
 * Grid Trading Pro
 * Enhanced grid trading bot with auto-adjust and multi-coin support
 */

class GridTrader {
  constructor(options = {}) {
    this.symbol = options.symbol || 'BTC/USDT';
    this.lowerPrice = options.lowerPrice || 40000;
    this.upperPrice = options.upperPrice || 50000;
    this.grids = options.grids || 20;
    this.investment = options.investment || 100;
    this.autoCompound = options.autoCompound || false;
    this.stopLoss = options.stopLoss || null;
    this.takeProfit = options.takeProfit || null;
    
    // State
    this.running = false;
    this.gridsData = [];
    this.trades = [];
    this.profit = 0;
    this.stats = {
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      totalProfit: 0
    };
    
    // Initialize grids
    this.initializeGrids();
  }
  
  /**
   * Initialize grid levels
   */
  initializeGrids() {
    const priceRange = this.upperPrice - this.lowerPrice;
    const gridSpacing = priceRange / this.grids;
    
    for (let i = 0; i <= this.grids; i++) {
      const price = this.lowerPrice + (i * gridSpacing);
      this.gridsData.push({
        level: i,
        price: price,
        filled: false,
        order: null
      });
    }
  }
  
  /**
   * Start grid trading
   */
  async start() {
    if (this.running) {
      throw new Error('Grid trader is already running');
    }
    
    this.running = true;
    console.log(`🚀 Starting grid trader for ${this.symbol}`);
    console.log(`   Range: $${this.lowerPrice} - $${this.upperPrice}`);
    console.log(`   Grids: ${this.grids}`);
    console.log(`   Investment: $${this.investment}`);
    
    // Place initial orders
    await this.placeInitialOrders();
    
    // Start monitoring
    this.monitorPrice();
  }
  
  /**
   * Stop grid trading
   */
  async stop() {
    this.running = false;
    console.log('⏹️  Grid trader stopped');
    
    // Cancel all orders
    await this.cancelAllOrders();
  }
  
  /**
   * Place initial grid orders
   */
  async placeInitialOrders() {
    console.log('📦 Placing initial grid orders...');
    
    // Simulate order placement
    for (const grid of this.gridsData) {
      // In real implementation, this would call exchange API
      grid.order = {
        id: `order-${grid.level}`,
        price: grid.price,
        side: grid.price < (this.lowerPrice + this.upperPrice) / 2 ? 'buy' : 'sell'
      };
    }
    
    console.log(`✅ Placed ${this.gridsData.length} grid orders`);
  }
  
  /**
   * Cancel all orders
   */
  async cancelAllOrders() {
    console.log('❌ Cancelling all orders...');
    
    for (const grid of this.gridsData) {
      grid.order = null;
      grid.filled = false;
    }
    
    console.log('✅ All orders cancelled');
  }
  
  /**
   * Monitor price and execute trades
   */
  async monitorPrice() {
    if (!this.running) return;
    
    // Simulate price monitoring
    setInterval(async () => {
      const currentPrice = await this.getCurrentPrice();
      
      // Check stop-loss
      if (this.stopLoss && currentPrice <= this.stopLoss) {
        console.log('⚠️  Stop-loss triggered!');
        await this.stop();
        return;
      }
      
      // Check take-profit
      if (this.takeProfit && currentPrice >= this.takeProfit) {
        console.log('✅ Take-profit triggered!');
        await this.stop();
        return;
      }
      
      // Execute grid trades
      await this.executeGridTrades(currentPrice);
      
    }, 5000); // Check every 5 seconds
  }
  
  /**
   * Get current price (simulate)
   */
  async getCurrentPrice() {
    // In real implementation, fetch from exchange
    const basePrice = (this.lowerPrice + this.upperPrice) / 2;
    const volatility = (this.upperPrice - this.lowerPrice) * 0.05;
    return basePrice + (Math.random() - 0.5) * volatility;
  }
  
  /**
   * Execute grid trades
   */
  async executeGridTrades(currentPrice) {
    for (const grid of this.gridsData) {
      const priceDiff = Math.abs(grid.price - currentPrice);
      const threshold = (this.upperPrice - this.lowerPrice) / this.grids / 2;
      
      if (priceDiff < threshold && !grid.filled) {
        // Execute trade
        grid.filled = true;
        this.stats.totalTrades++;
        
        const tradeProfit = Math.random() * 2 - 0.5; // Simulate profit/loss
        this.profit += tradeProfit;
        this.stats.totalProfit += tradeProfit;
        
        if (tradeProfit > 0) {
          this.stats.winningTrades++;
          console.log(`✅ Trade executed at $${grid.price.toFixed(2)} | Profit: $${tradeProfit.toFixed(2)}`);
        } else {
          this.stats.losingTrades++;
          console.log(`❌ Trade executed at $${grid.price.toFixed(2)} | Loss: $${tradeProfit.toFixed(2)}`);
        }
        
        // Auto-compound if enabled
        if (this.autoCompound && this.profit > 5) {
          await this.compoundProfits();
        }
      }
    }
  }
  
  /**
   * Compound profits
   */
  async compoundProfits() {
    const compoundAmount = this.profit * 0.5; // Compound 50%
    console.log(`💰 Compounding $${compoundAmount.toFixed(2)} of profits`);
    
    // Reinvest profits
    this.investment += compoundAmount;
    this.profit -= compoundAmount;
  }
  
  /**
   * Get trader status
   */
  getStatus() {
    return {
      running: this.running,
      symbol: this.symbol,
      investment: this.investment,
      profit: this.profit,
      roi: ((this.profit / this.investment) * 100).toFixed(2) + '%',
      gridsFilled: this.gridsData.filter(g => g.filled).length,
      totalTrades: this.stats.totalTrades,
      winningTrades: this.stats.winningTrades,
      losingTrades: this.stats.losingTrades
    };
  }
  
  /**
   * Get detailed report
   */
  getReport() {
    const status = this.getStatus();
    return {
      ...status,
      generatedAt: new Date().toISOString(),
      avgProfitPerTrade: (this.stats.totalProfit / this.stats.totalTrades).toFixed(2),
      winRate: ((this.stats.winningTrades / this.stats.totalTrades) * 100).toFixed(2) + '%',
      totalVolume: (this.stats.totalTrades * (this.investment / this.grids)).toFixed(2)
    };
  }
}

module.exports = { GridTrader };
