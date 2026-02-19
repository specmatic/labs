package com.store.services

import com.store.exceptions.ValidationException
import com.store.model.DB
import com.store.model.Id
import com.store.model.Product
import org.springframework.stereotype.Service

@Service
class ProductService {

    fun getProduct(id: Int): Product {
        return DB.findProduct(id)
    }

    fun updateProduct(product:Product){
        if(product.id == 0)
            throw ValidationException("Product id cannot be null")
        DB.updateProduct(product)
    }

    fun addProduct(product: Product): Id {
        DB.addProduct(product)
        return Id(product.id)
    }

    fun deleteProduct(id:Int) {
        DB.deleteProduct(id)
    }

    fun findProducts(name:String?, type:String?, status:String?): List<Product> {
        return DB.findProducts(name, type, status)
    }
}