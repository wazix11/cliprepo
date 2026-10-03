(() => {
    const endpoints = JSON.parse(document.getElementById('apiEndpoints').textContent);
    const endpointList = document.getElementById('endpointList');
    const endpointTitle = document.getElementById('endpointTitle');
    const endpointDescription = document.getElementById('endpointDescription');
    const requestPath = document.getElementById('requestPath');
    const endpointInput = document.getElementById('endpointInput');
    const queryParams = document.getElementById('queryParams');
    const queryParamsSection = document.getElementById('queryParamsSection');
    const parameterList = document.getElementById('parameterList');
    const codeExample = document.getElementById('codeExample');
    let selectedEndpoint = endpoints[0];
    let selectedLanguage = 'python';

    function queryString() {
        return queryParams.value.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
            const separator = line.indexOf('=');
            return separator > 0 ? `${encodeURIComponent(line.slice(0, separator).trim())}=${encodeURIComponent(line.slice(separator + 1).trim())}` : '';
        }).filter(Boolean).join('&');
    }

    function renderCodeExample() {
        const key = document.getElementById('apiKey').value || 'sk_your_api_key';
        const url = `${window.location.origin}${selectedEndpoint.path}${queryString() ? `?${queryString()}` : ''}`;
        const snippets = {
            python: `$ python -m pip install requests\nimport requests\n\nurl = "${url}"\n\nheaders = {\n    "accept": "application/json",\n    "Authorization": "Bearer ${key}",\n}\n\nresponse = requests.get(url, headers=headers)\nprint(response.text)`,
            javascript: `const url = "${url}";\nconst options = {\n    method: "GET",\n    headers: {\n        "accept": "application/json",\n        "Authorization": "Bearer ${key}",\n    }\n};\n\nfetch(url, options)\n    .then(res => res.json())\n    .then(json => console.log(json))\n    .catch(err => console.error(err));`,
            curl: `curl --request GET \\\n  --url "${url}" \\\n  --header "accept: application/json" \\\n  --header "Authorization: Bearer ${key}"`,
        };
        codeExample.textContent = snippets[selectedLanguage];
    }

    function renderEndpointDetails() {
        endpointTitle.textContent = selectedEndpoint.path;
        endpointDescription.textContent = selectedEndpoint.description;
        requestPath.textContent = selectedEndpoint.path;
        endpointInput.value = selectedEndpoint.path;
        const hasParameters = selectedEndpoint.parameters.length > 0;
        queryParamsSection.classList.toggle('d-none', !hasParameters);
        parameterList.innerHTML = hasParameters ? selectedEndpoint.parameters.map((parameter) => `<div class="param-row"><div><span class="param-name">${parameter.name}</span><span class="param-description">${parameter.description}</span></div><input class="form-control form-control-sm parameter-value" data-parameter="${parameter.name}" placeholder="Optional"></div>`).join('') : '';
        document.querySelectorAll('.endpoint').forEach((element) => element.classList.toggle('active', element.dataset.path === selectedEndpoint.path));
        renderCodeExample();
    }

    endpoints.forEach((endpoint) => {
        const item = document.createElement('button');
        item.className = 'endpoint w-100'; item.dataset.path = endpoint.path; item.type = 'button';
        item.innerHTML = `<span class="endpoint-path"><span class="method">GET</span>${endpoint.path}</span><span class="endpoint-description">${endpoint.description}</span>`;
        item.addEventListener('click', () => { selectedEndpoint = endpoint; renderEndpointDetails(); }); endpointList.appendChild(item);
    });

    function syncParameterValues() {
        queryParams.value = [...document.querySelectorAll('.parameter-value')].filter((input) => input.value.trim()).map((input) => `${input.dataset.parameter}=${input.value.trim()}`).join('\n'); renderCodeExample();
    }
    queryParams.addEventListener('input', renderCodeExample); document.getElementById('apiKey').addEventListener('input', renderCodeExample);
    document.addEventListener('input', (event) => { if (event.target.classList.contains('parameter-value')) syncParameterValues(); });
    document.querySelectorAll('.code-tab').forEach((tab) => tab.addEventListener('click', () => { selectedLanguage = tab.dataset.language; document.querySelectorAll('.code-tab').forEach((item) => item.classList.toggle('active', item === tab)); renderCodeExample(); }));
    renderEndpointDetails();
})();