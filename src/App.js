import React from 'react';
import './App.css';
import CropYieldForm from './components/CropYieldForm';

function App() {
  return (
    <div className="container">
      <h1 className="text-center text-success custom-heading mt-5 mb-4">Crop Yield Prediction Per Country</h1>
      <div className="row justify-content-center">
        <div className="col-lg-6">
          <CropYieldForm />
        </div>
      </div>
    </div>
  );
}

export default App;
