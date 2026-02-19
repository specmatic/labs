package com.store.controllers

import com.store.exceptions.NotFoundException
import com.store.exceptions.ValidationException
import com.store.model.Id
import com.store.model.Product
import com.store.model.User
import com.store.services.ProductService
import org.springframework.beans.factory.annotation.Autowired
import org.springframework.http.HttpStatus
import org.springframework.http.ResponseEntity
import org.springframework.security.core.annotation.AuthenticationPrincipal
import org.springframework.validation.annotation.Validated
import org.springframework.web.bind.annotation.*
import jakarta.validation.Valid

private val typesOfProducts = listOf("gadget", "book", "food", "other")

@RestController
open class Products {

    @Autowired
    lateinit var productService: ProductService

    @PostMapping("/products/{id}")
    @Validated
    fun update(
        @PathVariable id: Int,
        @Valid @RequestBody product: Product,
        @AuthenticationPrincipal user: User
    ): ResponseEntity<String> {
        productService.addProduct(product.also {
            if(product.type !in typesOfProducts)
                throw ValidationException("type must be one of ${typesOfProducts.joinToString(", ")}")
        })
        productService.updateProduct(product)
        return ResponseEntity(HttpStatus.OK)
    }

    @GetMapping("/products/{id}")
    fun get(@PathVariable("id") id: Int): Product {
        try {
            return productService.getProduct(id)
        } catch (e: NoSuchElementException) {
            throw NotFoundException(e.message!!)
        }
    }

    @PostMapping("/products")
    fun create(@Valid @RequestBody newProduct: Product, @AuthenticationPrincipal user: User): ResponseEntity<Id> {
        val productId = productService.addProduct(newProduct.also {
            if(newProduct.type !in typesOfProducts)
                throw ValidationException("type must be one of ${typesOfProducts.joinToString(", ")}")
        })
        return ResponseEntity(productId, HttpStatus.OK)
    }

    @DeleteMapping("/products/{id}")
    fun delete(@PathVariable("id") id: Int, @AuthenticationPrincipal user: User): ResponseEntity<String> {
        productService.deleteProduct(id)
        return ResponseEntity(HttpStatus.OK)
    }

    @GetMapping("/products")
    fun search(
        @RequestParam(name = "name", required = false) name: String?,
        @RequestParam(name = "type", required = false) type: String?,
        @RequestParam(name = "status", required = false) status: String?
    ): ResponseEntity<List<Product>> {
        // An exception thrown by some internal bug...
        if (name == "unknown")
            return ResponseEntity(HttpStatus.INTERNAL_SERVER_ERROR)
        val products = productService.findProducts(name, type, status)
        return ResponseEntity(products, HttpStatus.OK)
    }
}
