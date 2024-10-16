const chartData = {
     labels: ["On time", "Late", "Absent"],
     data: [70, 20, 10],
}

const myChart = document.querySelector(".my-chart");
const ul = document.querySelector(".child-stats .details ul");

new Chart(myChart, {
    type: "doughnut",
    data: {
        labels: chartData.labels,
        datasets: [
            {
                label: "Statistics",
                data: chartData.data,
            }
        ]
    },
    options: {
        borderWidth: 10,
        borderRadius: 1,
        hoverBorderWidth: 0,
        plugins: {
            legend: {
                display: false,
            }
        }
    }
});

const populateUl = () => {
    chartData.labels.forEach((l, i) => {
        let li = document.createElement("li");
        li.innerHTML = `${l}: <span class='percentage'>${chartData.data[i]}%</span>`;
        ul.appendChild(li);
    });
};

populateUl();

function openModal(event) {
    event.stopPropagation();  // Prevents the click event from affecting the accordion
    document.getElementById("myModal").style.display = "block";
}


function closeModal() {
    event.stopPropagation();
    document.getElementById("myModal").style.display = "none";
}

// Close the modal if the user clicks outside the modal content
window.onclick = function(event) {
    const modal = document.getElementById("myModal");
    if (event.target === modal) {
        modal.style.display = "none";
    }
}



function openModalProfile(event) {
    event.stopPropagation();  // Prevents the click event from affecting the accordion
    document.getElementById("modalProfile").style.display = "block";
}


function closeModalProfile() {
    event.stopPropagation();
    document.getElementById("modalProfile").style.display = "none";
}

// Close the modal if the user clicks outside the modal content
window.onclick = function(event) {
    const modal = document.getElementById("modalProfile");
    if (event.target === modal) {
        modal.style.display = "none";
    }
}



