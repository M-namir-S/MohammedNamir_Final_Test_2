#include <iostream>
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <limits>
struct LidarMetrics {
    float min_distance = 0.0f;
    float average_distance = 0.0f;
    size_t obstacles_detected = 0;
    std::ptrdiff_t closest_measurement_index = -1; // -1 indicates no valid data
};
LidarMetrics processLidarData(const std::vector<float>& ranges, float obstacle_threshold = 1.0f) {
    LidarMetrics metrics;
    struct ValidMeasurement {
        float distance;
        size_t original_index;
    };
    
    std::vector<ValidMeasurement> valid_data;
    valid_data.reserve(ranges.size()); 
    for (size_t i = 0; i < ranges.size(); ++i) {
        float val = ranges[i];
        if (!std::isnan(val) && !std::isinf(val) && val >= 0.0f) {
            valid_data.push_back({val, i});
        }
    }
    if (valid_data.empty()) {
        std::cerr << "Warning: No valid LiDAR measurements found after filtering.\n";
        return metrics;
    }
    auto min_it = std::min_element(valid_data.begin(), valid_data.end(), 
        [](const ValidMeasurement& a, const ValidMeasurement& b) {
            return a.distance < b.distance;
        });

    metrics.min_distance = min_it->distance;
    metrics.closest_measurement_index = min_it->original_index;
    float sum = std::accumulate(valid_data.begin(), valid_data.end(), 0.0f, 
        [](float acc, const ValidMeasurement& item) {
            return acc + item.distance;
        });
    metrics.average_distance = sum / valid_data.size();
    metrics.obstacles_detected = std::count_if(valid_data.begin(), valid_data.end(), 
        [obstacle_threshold](const ValidMeasurement& item) {
            return item.distance < obstacle_threshold;
        });

    return metrics;
}

int main() {
    std::vector<float> lidar_ranges = {
        12.5f, -0.5f, 0.8f, NAN, 1.5f, INFINITY, 0.4f, 3.2f, -INFINITY, 0.95f
    };

    const float OBSTACLE_THRESHOLD = 1.0f; 
    LidarMetrics result = processLidarData(lidar_ranges, OBSTACLE_THRESHOLD);
    if (result.closest_measurement_index != -1) {
        std::cout << "--- LiDAR Processing Report ---\n";
        std::cout << "Minimum distance: " << result.min_distance << " m\n";
        std::cout << "Average distance: " << result.average_distance << " m\n";
        std::cout << "Obstacles detected: " << result.obstacles_detected << "\n";
        std::cout << "Closest measurement index: " << result.closest_measurement_index << "\n";
    } else {
        std::cout << "Failed to process LiDAR dataset: Data is empty or entirely invalid.\n";
    }
    return 0;
}
